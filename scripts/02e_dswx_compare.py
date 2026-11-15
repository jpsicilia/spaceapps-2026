#!/usr/bin/env python
# AI-assisted: written with Claude (Anthropic) from the author’s specifications; reviewed and run by the author. See docs/ai_use.md
"""Step 2e: independent check of NISAR open water against OPERA DSWx-HLS (optical, 30 m).

DSWx-HLS B01_WTR codes: 0 not water, 1 open water, 2 partial surface water,
252 snow/ice, 253 cloud/cloud shadow, 254 ocean masked, 255 fill.

For each NISAR date, the closest DSWx date (|Δ| <= 5 days) is mosaicked onto the 40 m grid.
Metrics on pixels that are plain (NISAR classified) AND clear in DSWx (0/1/2):
  precision = NISAR water confirmed by DSWx open water; recall = DSWx open water found by NISAR;
  IoU. Partial surface water (2) is reported but left out of the confusion matrix.
Series: areas on pixels clear in ALL paired DSWx dates -> comparable through time.
Run from the repo root (after 02c):  python scripts/02e_dswx_compare.py
"""
from __future__ import annotations

import glob
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pantanal_sar.classify import NODATA, WATER, load_ladario_daily  # noqa: E402

MAX_DAYS = 5
CLEAR = (0, 1, 2)


def parse(fn):
    p = Path(fn).name.split("_")
    return p[3], p[4][:8], p[6]  # tile, YYYYMMDD, sensor


def mosaic(files, grid):
    """Nearest-neighbour mosaic on the grid; clear pixels win over cloud, cloud over fill."""
    out = np.full(grid["shape"], 255, dtype="uint8")
    for f in files:
        tmp = np.full(grid["shape"], 255, dtype="uint8")
        with rasterio.open(f) as s:
            reproject(s.read(1), tmp, src_transform=s.transform, src_crs=s.crs,
                      dst_transform=grid["transform"], dst_crs=grid["crs"],
                      src_nodata=255, dst_nodata=255, resampling=Resampling.nearest)
        tclear, oclear = np.isin(tmp, CLEAR), np.isin(out, CLEAR)
        out[tclear & ~oclear] = tmp[tclear & ~oclear]
        out[(out == 255) & (tmp == 253)] = 253
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-clear", type=float, default=80.0,
                    help="pairs with less clear plain (%%) are left out of the common-pixel series")
    args = ap.parse_args()
    proc, tabs, figs = (ROOT / p for p in ("data/processed", "outputs/tables", "outputs/figures"))
    dswx_files = sorted(glob.glob(str(ROOT / "data/raw/opera_dswx/*_B01_WTR.tif")))
    by_date = defaultdict(list)
    for f in dswx_files:
        by_date[parse(f)[1]].append(f)
    cls_files = sorted(glob.glob(str(proc / "class_*.tif")))
    nisar_dates = [Path(f).stem.split("_")[1] for f in cls_files]
    print(f"[1/4] DSWx: {len(dswx_files)} files, {len(by_date)} dates: {', '.join(sorted(by_date))}")
    print(f"      NISAR classes: {', '.join(nisar_dates)}")

    with rasterio.open(cls_files[0]) as r:
        grid = dict(transform=r.transform, crs=r.crs, shape=r.shape)
        pix_area = abs(r.transform.a * r.transform.e)
    km2 = lambda m: m.sum() * pix_area / 1e6  # noqa: E731

    cls = {}
    for d, f in zip(nisar_dates, cls_files):
        with rasterio.open(f) as r:
            cls[d] = r.read(1)
    plain = np.logical_and.reduce([c != NODATA for c in cls.values()])

    # mosaic every DSWx date once (cheap) and pair by closest date, tie -> more clear pixels
    mos = {d: mosaic(fs, grid) for d, fs in by_date.items()}
    clear_frac = {d: np.isin(m[plain], CLEAR).mean() for d, m in mos.items()}
    pairs = {}
    for nd in nisar_dates:
        t = datetime.strptime(nd, "%Y%m%d")
        cands = [(abs((datetime.strptime(dd, "%Y%m%d") - t).days), -clear_frac[dd], dd) for dd in mos]
        cands = [c for c in cands if c[0] <= MAX_DAYS]
        if cands:
            pairs[nd] = min(cands)[2]
    print("      pairs (NISAR <- DSWx, clear % of plain): " +
          " | ".join(f"{n[4:]}<-{d[4:]} ({100 * clear_frac[d]:.0f}%)" for n, d in pairs.items()))
    if not pairs:
        sys.exit("[ERROR] no DSWx date within ±5 days of any NISAR date")

    # ------------------------------------------------- per-pair agreement
    rows = []
    for nd, dd in pairs.items():
        w = mos[dd]
        clear = plain & np.isin(w, CLEAR)
        nw = (cls[nd] == WATER) & clear
        dw = (w == 1) & clear
        conf = clear & (w != 2)
        tp, fp, fn = km2(nw & dw & conf), km2(nw & ~dw & conf), km2(~nw & dw & conf)
        rows.append(dict(
            nisar_date=nd, dswx_date=dd, sensors="+".join(sorted({parse(f)[2] for f in by_date[dd]})),
            clear_pct=100 * clear.sum() / plain.sum(),
            nisar_water_km2=km2(nw), dswx_open_km2=km2(dw), dswx_partial_km2=km2((w == 2) & clear),
            precision=tp / (tp + fp) if tp + fp else np.nan,
            recall=tp / (tp + fn) if tp + fn else np.nan,
            iou=tp / (tp + fp + fn) if tp + fp + fn else np.nan,
        ))
    df = pd.DataFrame(rows)
    df.to_csv(tabs / "dswx_agreement_all_pairs.csv", index=False, float_format="%.3f")
    print(f"[2/4] agreement per pair (clear pixels; partial water excluded from P/R/IoU):")
    with pd.option_context("display.width", 220, "display.max_columns", 30):
        print(df[["nisar_date", "dswx_date", "sensors", "clear_pct", "nisar_water_km2", "dswx_open_km2",
                  "dswx_partial_km2", "precision", "recall", "iou"]].round(2).to_string(index=False))

    # ------------------------------------------------- consistent series
    keep = df["clear_pct"] >= args.min_clear
    dropped = df.loc[~keep, "nisar_date"].tolist()
    if dropped:
        print(f"      series: leaving out pairs with < {args.min_clear:.0f}% clear: {dropped}")
    if keep.sum() < 3:
        sys.exit(f"[ERROR] fewer than 3 pairs with >= {args.min_clear}% clear; lower --min-clear")
    df = df[keep].reset_index(drop=True)
    pairs = {n: d for n, d in pairs.items() if n in set(df["nisar_date"])}
    clear_all = plain & np.logical_and.reduce([np.isin(mos[dd], CLEAR) for dd in pairs.values()])
    ca = 100 * clear_all.sum() / plain.sum()
    df["series_nisar_km2"] = [km2((cls[nd] == WATER) & clear_all) for nd in pairs]
    df["series_dswx_open_km2"] = [km2((mos[dd] == 1) & clear_all) for dd in pairs.values()]
    df["series_dswx_open_partial_km2"] = [km2(np.isin(mos[dd], (1, 2)) & clear_all) for dd in pairs.values()]

    daily, _ = load_ladario_daily(ROOT / "data/external/ladario_gauge/ladario_stage_raw_telemetria.csv",
                                  verbose=False)
    df["stage_at_dswx_cm"] = [daily["stage"].get(pd.Timestamp(f"{d[:4]}-{d[4:6]}-{d[6:]}"), np.nan)
                              for d in df["dswx_date"]]
    df.to_csv(tabs / "dswx_comparison.csv", index=False, float_format="%.3f")

    print(f"[3/4] series on pixels clear in ALL paired DSWx dates ({ca:.0f}% of plain, "
          f"{km2(clear_all):,.0f} km²):")
    print(df[["nisar_date", "dswx_date", "series_nisar_km2", "series_dswx_open_km2",
              "series_dswx_open_partial_km2", "stage_at_dswx_cm"]].round(1).to_string(index=False))
    ok = df.dropna(subset=["stage_at_dswx_cm"])
    if len(ok) >= 4:
        for col in ["series_dswx_open_km2", "series_dswx_open_partial_km2", "series_nisar_km2"]:
            r, pr = stats.pearsonr(ok["stage_at_dswx_cm"], ok[col])
            rho, ps = stats.spearmanr(ok["stage_at_dswx_cm"], ok[col])
            print(f"      {col:30} vs Ladário: r={r:.2f} (p={pr:.3f})  ρ={rho:.2f} (p={ps:.3f})")
        r, pr = stats.pearsonr(ok["series_nisar_km2"], ok["series_dswx_open_km2"])
        print(f"      NISAR vs DSWx open (same pixels): r={r:.2f} (p={pr:.3f}); "
              f"mean ratio NISAR/DSWx = {np.mean(ok['series_nisar_km2'] / ok['series_dswx_open_km2']):.2f}")

    # ------------------------------------------------- figures
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    tn = pd.to_datetime(df["nisar_date"])
    td = pd.to_datetime(df["dswx_date"])
    ax.plot(tn, df["series_nisar_km2"], "o-", color="#1f4e9c", label="NISAR open water (L-band SAR)")
    ax.plot(td, df["series_dswx_open_km2"], "s-", color="#e6550d", label="DSWx-HLS open water (optical)")
    ax.plot(td, df["series_dswx_open_partial_km2"], "s--", color="#fdae6b", label="DSWx-HLS open + partial")
    ax.set_ylabel(f"area on common clear pixels (km², {ca:.0f}% of plain)")
    a2 = ax.twinx()
    st = daily.loc[tn.min() - pd.Timedelta(days=10): tn.max() + pd.Timedelta(days=10), "stage"]
    a2.plot(st.index, st.values, color="0.5", lw=1)
    a2.set_ylabel("Ladário stage (cm)", color="0.4")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title("Open water: NISAR vs OPERA DSWx-HLS vs Ladário stage")
    fig.savefig(figs / "nisar_vs_dswx_series.png", dpi=120)
    plt.close(fig)

    best = df.sort_values(["clear_pct"], ascending=False).iloc[0]
    nd, dd = best["nisar_date"], best["dswx_date"]
    w = mos[dd]
    clear = plain & np.isin(w, CLEAR)
    nw, dw = cls[nd] == WATER, w == 1
    img = np.full(w.shape, 0, dtype="uint8")          # 0 outside / masked
    img[plain] = 1                                     # land both
    img[plain & ~clear] = 2                            # cloud in DSWx
    img[clear & nw & dw] = 3                           # agree water
    img[clear & nw & ~dw & (w != 2)] = 4               # NISAR only
    img[clear & ~nw & dw] = 5                          # DSWx only
    img[clear & (w == 2)] = 6                          # DSWx partial
    cm = ListedColormap(["#ffffff", "#efe6cf", "#bdbdbd", "#1f4e9c", "#d62728", "#ff9f1c", "#9ecae1"])
    labels = ["", "land (both)", "cloud (DSWx)", "water: both agree", "water: NISAR only",
              "water: DSWx only", "DSWx partial water"]
    fig, ax = plt.subplots(figsize=(8, 11), constrained_layout=True)
    ax.imshow(img, cmap=cm, vmin=0, vmax=6, interpolation="nearest")
    ax.legend(handles=[Patch(color=cm(k), label=labels[k]) for k in range(1, 7)], loc="lower left", fontsize=8)
    ax.set_title(f"Agreement NISAR {nd} vs DSWx-HLS {dd}  (IoU {best['iou']:.2f})")
    ax.set_axis_off()
    fig.savefig(figs / f"agreement_{nd}_dswx_{dd}.png", dpi=220)
    # same map without axes/legend, one pixel per 40 m cell, for the slides (legend drawn there)
    from PIL import Image
    rgba = (np.array([cm(k) for k in range(7)]) * 255).astype("uint8")
    rgba[0, 3] = 0
    Image.fromarray(rgba[img]).save(figs / f"agreement_raw_{nd}_dswx_{dd}.png", optimize=True)
    plt.close(fig)
    print(f"[4/4] figures: {figs}/nisar_vs_dswx_series.png, agreement_{nd}_dswx_{dd}.png")


if __name__ == "__main__":
    main()
