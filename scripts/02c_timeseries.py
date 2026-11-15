#!/usr/bin/env python
"""Step 2c: classify all dates with the FIXED thresholds, area series vs Ladário,
change map 17 Jul -> 21 Oct, hydroperiod.

Inputs : data/processed/gcov_*_40m_db.tif, data/processed/masks_40m.tif, config/thresholds.yaml
Outputs: data/processed/class_<date>.tif
         outputs/tables/area_series.csv, outputs/tables/change_20260717_20261021.csv
         outputs/maps/change_20260717_20261021.tif, outputs/maps/hydroperiod.tif
         outputs/figures/area_vs_stage.png, change_20260717_20261021.png, hydroperiod.png
Run from the repo root:  python scripts/02c_timeseries.py
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pantanal_sar.classify import (  # noqa: E402
    FLOODVEG, LAND, NODATA, WATER, classify, control_water_pct, jrc_permanent_on_grid,
    load_ladario_daily, ref_grid, remove_small,
)


def read_thresholds(path):
    th = {}
    for line in Path(path).read_text().splitlines():
        line = line.split("#")[0].strip()
        if ":" in line:
            k, v = line.split(":", 1)
            th[k.strip()] = float(v)
    return th


def read_on_grid(tif, grid):
    """Read HH, HV dB on the reference grid (nearest if the grid differs)."""
    with rasterio.open(tif) as r:
        if r.transform == grid["transform"] and r.shape == grid["shape"]:
            return r.read(1), r.read(2), True
        out = []
        for b in (1, 2):
            dst = np.full(grid["shape"], np.nan, dtype="float32")
            reproject(r.read(b), dst, src_transform=r.transform, src_crs=r.crs,
                      dst_transform=grid["transform"], dst_crs=grid["crs"],
                      src_nodata=np.nan, dst_nodata=np.nan, resampling=Resampling.nearest)
            out.append(dst)
        return out[0], out[1], False


def write_u8(path, arr, grid, descr, nodata=255):
    prof = dict(driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1, dtype="uint8",
                crs=grid["crs"], transform=grid["transform"], nodata=nodata, compress="deflate")
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(arr.astype("uint8"), 1)
        dst.set_band_description(1, descr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref-date", default="20260717")
    ap.add_argument("--change-to", default="20261021")
    ap.add_argument("--gauge", default=str(ROOT / "data/external/ladario_gauge/ladario_stage_raw_telemetria.csv"))
    ap.add_argument("--jrc-dir", default=str(ROOT / "data/external/jrc_gsw"))
    ap.add_argument("--normalize", action="store_true",
                    help="shift thresholds per date by the stable-zone (hills) offset from 02d")
    args = ap.parse_args()

    proc, tabs, maps, figs = (ROOT / p for p in ("data/processed", "outputs/tables", "outputs/maps", "outputs/figures"))
    for d in (tabs, maps, figs):
        d.mkdir(parents=True, exist_ok=True)

    th = read_thresholds(ROOT / "config/thresholds.yaml")
    min_px = int(th["mmu_px"])
    print("[1/5] thresholds:", {k: v for k, v in th.items()})

    files = sorted(glob.glob(str(proc / "gcov_*_40m_db.tif")))
    dates = [Path(f).name.split("_")[1] for f in files]
    print(f"      {len(dates)} dates: {', '.join(dates)}")
    if len(dates) < 8:
        print("      [WARN] fewer than 8 dates -> did scripts/02a_preprocess_all.sh finish?")

    grid = ref_grid(proc / f"gcov_{args.ref_date}_40m_db.tif")
    pix_area = abs(grid["transform"].a * grid["transform"].e)
    with rasterio.open(proc / "masks_40m.tif") as m:
        urban, high, dem, perm90 = (m.read(i) for i in (1, 2, 3, 4))
    plain = (urban == 0) & (high == 0) & np.isfinite(dem)
    perm90 = (perm90 == 1) & plain
    core = jrc_permanent_on_grid(args.jrc_dir, grid, occ_min=98, erode_px=2)[0] & plain
    print(f"      control zones inside plain: JRC>90% {perm90.sum() * pix_area / 1e6:.0f} km² | "
          f"core JRC>=98% eroded 2px {core.sum() * pix_area / 1e6:.0f} km²")

    offsets = {}
    if args.normalize:
        import pandas as pd
        stab = pd.read_csv(tabs / "stability.csv", dtype={"date": str}).set_index("date")
        offsets = {d: (float(stab.loc[d, "d_hh_stable"]), float(stab.loc[d, "d_hv_stable"])) for d in stab.index}
        print("      NORMALIZED: per-date threshold shift from hills (DEM>200 m), dB: " +
              " ".join(f"{d[4:]}:{o[0]:+.2f}/{o[1]:+.2f}" for d, o in offsets.items()))

    def th_for(d):
        if d not in offsets:
            return th
        dhh, dhv = offsets[d]
        t = dict(th)
        t["water_hh_max"] += dhh
        t["water_hv_max"] += dhv
        t["floodveg_hh_min"] += dhh
        t["floodveg_diff_min"] += dhh - dhv
        return t

    # ------------------------------------------------------------ classify
    cls_stack, med = {}, {}
    for d, f in zip(dates, files):
        hh, hv, same = read_on_grid(f, grid)
        cls = remove_small(classify(hh, hv, th_for(d), plain), min_px)
        cls_stack[d] = cls
        med[d] = (float(np.nanmedian(hh[plain])), float(np.nanmedian(hv[plain])))
        write_u8(proc / f"class_{d}.tif", cls, grid, "0 nodata,1 water,2 flooded veg,3 land", nodata=0)
        if not same:
            print(f"      [INFO] {d}: grid differed, resampled (nearest) to {args.ref_date} grid")

    common = np.logical_and.reduce([c != NODATA for c in cls_stack.values()])
    lost = 100 * (1 - common.sum() / plain.sum())
    print(f"[2/5] common valid area (all dates): {common.sum() * pix_area / 1e6:,.0f} km² "
          f"({lost:.1f}% of plain lost to nodata in some date)")

    # ---------------------------------------------------------- series
    import pandas as pd
    from scipy import stats

    daily, _ = load_ladario_daily(args.gauge, verbose=False)
    rows = []
    for d in dates:
        c = np.where(common, cls_stack[d], NODATA)
        key = pd.Timestamp(f"{d[:4]}-{d[4:6]}-{d[6:]}")
        st = daily["stage"].get(key, np.nan)
        rows.append(dict(
            date=key.date(), water_km2=(c == WATER).sum() * pix_area / 1e6,
            floodveg_km2=(c == FLOODVEG).sum() * pix_area / 1e6,
            land_km2=(c == LAND).sum() * pix_area / 1e6,
            ctrl90_water_pct=control_water_pct(cls_stack[d], perm90),
            core_water_pct=control_water_pct(cls_stack[d], core),
            hh_med_plain=med[d][0], hv_med_plain=med[d][1],
            stage_cm=st, stage_n=int(daily["n_obs"].get(key, 0)),
            normalized=bool(offsets),
        ))
    df = pd.DataFrame(rows)
    flag_col = "core_water_pct" if core.sum() >= 50 else "ctrl90_water_pct"
    if flag_col != "core_water_pct":
        print("      [WARN] core control zone too small; wind flag uses the JRC>90% zone")
    df["flag"] = np.where(df[flag_col] < df[flag_col].median() - 10, "WIND?", "")
    df.to_csv(tabs / "area_series.csv", index=False, float_format="%.3f")
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(df.round(2).to_string(index=False))

    ok = df.dropna(subset=["stage_cm"])
    okc = ok[ok["flag"] == ""]
    print("[3/5] water area vs Ladário stage:")
    for name, sub in [("all dates", ok), ("excluding WIND? flags", okc)]:
        if len(sub) >= 4:
            r, pr = stats.pearsonr(sub["stage_cm"], sub["water_km2"])
            rho, ps = stats.spearmanr(sub["stage_cm"], sub["water_km2"])
            fit = stats.linregress(sub["stage_cm"], sub["water_km2"])
            print(f"      {name:22} n={len(sub)}  Pearson r={r:.2f} (p={pr:.3f})  "
                  f"Spearman ρ={rho:.2f} (p={ps:.3f})  slope={fit.slope:.2f} km²/cm")

    # ----------------------------------------------------- change map
    a, b = cls_stack[args.ref_date], cls_stack.get(args.change_to)
    if b is not None:
        chg = np.full(a.shape, 255, dtype="uint8")
        v = common
        wa, wb = a == WATER, b == WATER
        fa, fb = a == FLOODVEG, b == FLOODVEG
        chg[v] = 0                                   # stable land
        chg[v & wa & wb] = 1                         # water both dates
        chg[v & wa & ~wb] = 2                        # water lost (drained)
        chg[v & ~wa & wb] = 3                        # water gained
        chg[v & fa & ~fb & ~wb] = 4                  # flooded veg lost
        chg[v & ~fa & fb] = 5                        # flooded veg gained
        chg[v & fa & fb] = 6                         # flooded veg both
        names = {0: "stable land", 1: "water both", 2: "water lost", 3: "water gained",
                 4: "flooded veg lost", 5: "flooded veg gained", 6: "flooded veg both"}
        ct = pd.DataFrame([dict(code=k, transition=n, km2=(chg == k).sum() * pix_area / 1e6)
                           for k, n in names.items()])
        ct.to_csv(tabs / f"change_{args.ref_date}_{args.change_to}.csv", index=False, float_format="%.2f")
        write_u8(maps / f"change_{args.ref_date}_{args.change_to}.tif", chg, grid,
                 "; ".join(f"{k} {n}" for k, n in names.items()))
        print(f"[4/5] change {args.ref_date} -> {args.change_to}: " +
              " | ".join(f"{r.transition} {r.km2:,.1f}" for r in ct.itertuples() if r.code))
    else:
        print(f"[4/5] [WARN] no {args.change_to} classification; change map skipped")
        chg = None

    # ------------------------------------------------------- hydroperiod
    n = len(dates)
    wcount = sum((c == WATER).astype("uint8") for c in cls_stack.values())
    icount = sum(((c == WATER) | (c == FLOODVEG)).astype("uint8") for c in cls_stack.values())
    hyd = np.where(common, wcount, 255).astype("uint8")
    write_u8(maps / "hydroperiod.tif", hyd, grid, f"number of dates (of {n}) classified open water")
    hist = np.bincount(wcount[common], minlength=n + 1)
    print(f"[5/5] hydroperiod (dates as open water, of {n}): " +
          " ".join(f"{k}:{hist[k] * pix_area / 1e6:,.0f}" for k in range(n + 1)) + "  (km²)")
    print(f"      inundated (water or flooded veg) ≥1 date: {(icount[common] > 0).sum() * pix_area / 1e6:,.0f} km²")

    # ----------------------------------------------------------- figures
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap

    fig, ax = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    t = pd.to_datetime(df["date"])
    ax[0].plot(t, df["water_km2"], "o-", color="#1f4e9c", label="open water (NISAR)")
    ax[0].set_ylabel("open water area (km²)", color="#1f4e9c")
    for _, r in df[df["flag"] != ""].iterrows():
        ax[0].annotate("wind?", (pd.Timestamp(r["date"]), r["water_km2"]), textcoords="offset points",
                       xytext=(0, 8), ha="center", fontsize=8, color="red")
    a2 = ax[0].twinx()
    st = daily.loc[t.min() - pd.Timedelta(days=10): t.max() + pd.Timedelta(days=10), "stage"]
    a2.plot(st.index, st.values, color="0.5", lw=1, label="Ladário stage (daily mean)")
    a2.set_ylabel("Ladário stage (cm)", color="0.4")
    ax[0].set_title("NISAR open-water area vs Paraguay River stage at Ladário")
    ax[1].scatter(ok["stage_cm"], ok["water_km2"], c="#1f4e9c")
    for _, r in ok.iterrows():
        ax[1].annotate(str(r["date"])[5:], (r["stage_cm"], r["water_km2"]), fontsize=8,
                       textcoords="offset points", xytext=(4, 4))
    if len(ok) >= 4:
        fit = stats.linregress(ok["stage_cm"], ok["water_km2"])
        xs = np.linspace(ok["stage_cm"].min(), ok["stage_cm"].max(), 10)
        ax[1].plot(xs, fit.intercept + fit.slope * xs, "k--",
                   label=f"r = {fit.rvalue:.2f}, slope = {fit.slope:.2f} km²/cm")
        ax[1].legend()
    ax[1].set_xlabel("Ladário stage (cm)")
    ax[1].set_ylabel("open water area (km²)")
    ax[1].set_title("Area–stage relation")
    fig.savefig(figs / "area_vs_stage.png", dpi=120)
    plt.close(fig)

    if chg is not None:
        cm = ListedColormap(["#efe6cf", "#1f4e9c", "#e6550d", "#6baed6", "#fdae6b", "#74c476", "#238b45"])
        img = np.ma.masked_equal(chg, 255)
        fig, ax = plt.subplots(figsize=(8, 11), constrained_layout=True)
        ax.imshow(img, cmap=cm, vmin=0, vmax=6, interpolation="nearest")
        from matplotlib.patches import Patch
        ax.legend(handles=[Patch(color=cm(k), label=names[k]) for k in names], loc="lower left", fontsize=8)
        ax.set_title(f"Change {args.ref_date} → {args.change_to}")
        ax.set_axis_off()
        fig.savefig(figs / f"change_{args.ref_date}_{args.change_to}.png", dpi=120)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 11), constrained_layout=True)
    im = ax.imshow(np.ma.masked_equal(hyd, 255), cmap="Blues", vmin=0, vmax=n, interpolation="nearest")
    fig.colorbar(im, ax=ax, shrink=0.5, label=f"dates as open water (of {n})")
    ax.set_title(f"Hydroperiod {dates[0]}–{dates[-1]}")
    ax.set_axis_off()
    fig.savefig(figs / "hydroperiod.png", dpi=120)
    plt.close(fig)
    print(f"      figures: {figs}/area_vs_stage.png, change_*.png, hydroperiod.png")


if __name__ == "__main__":
    main()
