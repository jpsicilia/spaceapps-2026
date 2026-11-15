#!/usr/bin/env python
# AI-assisted: written with Claude (Anthropic) from the author’s specifications; reviewed and run by the author. See docs/ai_use.md
"""Step 2b: masks (urban OSM + DEM height) + threshold calibration on 2026-07-17 + Ladário check.

Writes:
  data/processed/masks_40m.tif        band1 = urban, band2 = high terrain, band3 = DEM (m)
  config/thresholds.yaml              fixed thresholds used for ALL dates (edit by hand if needed)
  outputs/figures/calib_hist_20260717.png
  outputs/figures/class_preview_20260717.png
Run from the repo root:  python scripts/02b_calibrate.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pantanal_sar.classify import (  # noqa: E402
    FLOODVEG, LAND, WATER, bimodal_tiles, class_areas_km2, classify, control_water_pct,
    dem_on_grid, jrc_permanent_on_grid, load_ladario_daily, otsu, physical_check, ref_grid,
    remove_small, robust_upper, sigma0_to_gamma0, urban_on_grid,
)

DATES = ["20260717", "20260810", "20260822", "20260903", "20260915",
         "20260927", "20261009", "20261021", "20261102"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default=str(ROOT / "data/processed/gcov_20260717_40m_db.tif"))
    ap.add_argument("--dem-dir", default=str(ROOT / "data/external/dem"))
    ap.add_argument("--urban-dir", default=str(ROOT / "data/external/urban_mask"))
    ap.add_argument("--jrc-dir", default=str(ROOT / "data/external/jrc_gsw"))
    ap.add_argument("--gauge", default=str(ROOT / "data/external/ladario_gauge/ladario_stage_raw_telemetria.csv"))
    ap.add_argument("--max-height", type=float, default=135.0, help="plain upper limit (m)")
    ap.add_argument("--mmu-ha", type=float, default=1.0)
    ap.add_argument("--k", type=float, default=1.5, help="k for flooded-veg robust thresholds")
    ap.add_argument("--water-q", type=float, default=99.0, help="percentile of control zone used as water thr")
    ap.add_argument("--cap-hv", type=float, default=-22.0, help="max HV water thr (gamma0 dB)")
    ap.add_argument("--cap-hh", type=float, default=-16.0, help="max HH water thr (gamma0 dB)")
    args = ap.parse_args()

    grid = ref_grid(args.ref)
    px = abs(grid["transform"].a)
    pix_area = px * abs(grid["transform"].e)
    min_px = int(np.ceil(args.mmu_ha * 1e4 / pix_area))
    with rasterio.open(args.ref) as r:
        hh, hv = r.read(1), r.read(2)
        profile = r.profile
    valid = np.isfinite(hh) & np.isfinite(hv)

    # ---------------------------------------------------------------- masks
    dem, dem_files = dem_on_grid(args.dem_dir, grid)
    urban, urb_files = urban_on_grid(args.urban_dir, grid)
    high = np.isfinite(dem) & (dem > args.max_height)
    plain = valid & ~urban & ~high & np.isfinite(dem)
    n = valid.sum()
    print(f"[1/4] DEM files: {len(dem_files)} -> {[Path(f).name for f in dem_files][:4]}")
    print(f"      DEM inside valid SAR: p1/p50/p99 = "
          f"{np.nanpercentile(dem[valid], 1):.0f} / {np.nanpercentile(dem[valid], 50):.0f} / "
          f"{np.nanpercentile(dem[valid], 99):.0f} m  (max {np.nanmax(dem[valid]):.0f})")
    print(f"      Urban files: {[Path(f).name for f in urb_files][:4]}")
    print(f"      masked: urban {100 * (urban & valid).sum() / n:.2f}% | "
          f">{args.max_height:.0f} m {100 * (high & valid).sum() / n:.2f}% | "
          f"analysed plain {100 * plain.sum() / n:.1f}% | MMU {args.mmu_ha} ha = {min_px} px")

    perm, jrc_files = jrc_permanent_on_grid(args.jrc_dir, grid)
    perm &= valid & ~urban
    print(f"      JRC control zone (occurrence > 90%, 1-px eroded): {perm.sum():,} px = "
          f"{perm.sum() * pix_area / 1e6:,.1f} km²  [{Path(jrc_files[0]).name}]")

    mprof = profile.copy()
    mprof.update(count=4, dtype="float32", nodata=np.nan)
    with rasterio.open(ROOT / "data/processed/masks_40m.tif", "w", **mprof) as dst:
        dst.write(urban.astype("float32"), 1)
        dst.write(high.astype("float32"), 2)
        dst.write(dem, 3)
        dst.write(perm.astype("float32"), 4)
        for i, d in enumerate(["urban", f"dem_gt_{int(args.max_height)}m", "dem_m", "jrc_occ_gt90"], 1):
            dst.set_band_description(i, d)

    # ----------------------------------------------------------- thresholds
    # Water: calibrated on the JRC permanent-water zone (known water), capped at HV -22 / HH -16 dB gamma0.
    q = (50, 95, 99)
    php, pvp = np.percentile(hh[perm], q), np.percentile(hv[perm], q)
    print(f"[2/4] Water calibrated on JRC control zone ({perm.sum():,} px):")
    print(f"      HH  p50/p95/p99 = {php[0]:6.2f} / {php[1]:6.2f} / {php[2]:6.2f} dB")
    print(f"      HV  p50/p95/p99 = {pvp[0]:6.2f} / {pvp[1]:6.2f} / {pvp[2]:6.2f} dB")
    p_hh, p_hv = np.percentile(hh[perm], args.water_q), np.percentile(hv[perm], args.water_q)
    t_hh_w, t_hv = min(p_hh, args.cap_hh), min(p_hv, args.cap_hv)
    print(f"      -> HV thr = min(p{args.water_q:.0f} {p_hv:.2f}, cap {args.cap_hv}) = {t_hv:.2f} dB"
          f"{'  [CAP]' if p_hv > args.cap_hv else ''}")
    print(f"      -> HH thr = min(p{args.water_q:.0f} {p_hh:.2f}, cap {args.cap_hh}) = {t_hh_w:.2f} dB"
          f"{'  [CAP]' if p_hh > args.cap_hh else ''}")
    tiles, ntiles = bimodal_tiles(hv, plain)
    print(f"      (reference only) Otsu on {ntiles} bimodal tiles: HV {otsu(hv[tiles]):.2f}, "
          f"HH {otsu(hh[tiles]):.2f} | global Otsu HV {otsu(hv[plain]):.2f}")
    raw_w = plain & (hv < t_hv) & (hh < t_hh_w)
    print(f"      raw water (before MMU): {100 * raw_w.sum() / plain.sum():.2f}% of plain")

    nonwater = plain & ~raw_w
    t_hh_fv, med_hh, sig_hh = robust_upper(hh[nonwater], args.k)
    t_d_fv, med_d, sig_d = robust_upper((hh - hv)[nonwater], args.k)
    print(f"      Flooded veg (median + {args.k}·σMAD over non-water plain):")
    print(f"      HH    > {t_hh_fv:.2f} dB  (median {med_hh:.2f}, σ {sig_hh:.2f})")
    print(f"      HH−HV > {t_d_fv:.2f} dB  (median {med_d:.2f}, σ {sig_d:.2f})")

    th = dict(water_hv_max=round(t_hv, 2), water_hh_max=round(t_hh_w, 2),
              floodveg_hh_min=round(t_hh_fv, 2), floodveg_diff_min=round(t_d_fv, 2),
              max_height_m=args.max_height, mmu_ha=args.mmu_ha, mmu_px=min_px)
    yaml_txt = (
        "# Fixed thresholds calibrated on 2026-07-17 (scripts/02b_calibrate.py); applied to ALL dates.\n"
        f"# water: HV < water_hv_max AND HH < water_hh_max  (p{args.water_q:.0f} of JRC occurrence>90% zone, "
        f"capped at HV {args.cap_hv} / HH {args.cap_hh})\n"
        "# flooded vegetation: HH > floodveg_hh_min AND HH-HV > floodveg_diff_min "
        f"(median + {args.k} sigma_MAD over non-water plain)\n"
        + "".join(f"{k}: {v}\n" for k, v in th.items())
    )
    (ROOT / "config/thresholds.yaml").write_text(yaml_txt)

    lo_off, hi_off, off_src = sigma0_to_gamma0()
    print("      Physical check vs Evans (2013) L-band sigma0, open vs vegetated lakes "
          f"(gamma0 − sigma0 = {lo_off:+.2f} to {hi_off:+.2f} dB, {off_src}):")
    for key, v, ref, flag, note in physical_check(th):
        print(f"        {flag:4} {key:18} = {v:7.2f} dB   expected {ref:16}  {note}")

    # --------------------------------------------------------- preview
    # control zone is classified even if >135 m DEM/urban rules would drop it (it never is)
    cls = remove_small(classify(hh, hv, th, plain), min_px)
    print(f"      Control zone classified as open water: {control_water_pct(cls, perm):.1f}%"
          f"  (high by construction; independent check = 8-date series vs Ladário)")
    # where does flooded vegetation fall?
    from scipy import ndimage
    perm_full = jrc_permanent_on_grid(args.jrc_dir, grid, erode_px=0)[0]
    dist_km = ndimage.distance_transform_edt(~perm_full) * px / 1000
    fv = cls == FLOODVEG
    if fv.any():
        lab, nfv = ndimage.label(fv, structure=np.ones((3, 3), bool))
        sizes = np.bincount(lab.ravel())[1:] * pix_area / 1e4
        d = dist_km[fv]
        print(f"      Flooded veg: {nfv} patches, median {np.median(sizes):.1f} ha, "
              f"largest {sizes.max():,.0f} ha, top-10 patches = {100 * np.sort(sizes)[-10:].sum() / sizes.sum():.0f}% of area")
        print(f"      Flooded veg distance to permanent water: ≤1 km {100 * np.mean(d <= 1):.0f}% | "
              f"≤2 km {100 * np.mean(d <= 2):.0f}% | ≤5 km {100 * np.mean(d <= 5):.0f}% | median {np.median(d):.1f} km")
        print(f"      (for comparison, all plain pixels ≤2 km: {100 * np.mean(dist_km[plain] <= 2):.0f}%)")
    areas = class_areas_km2(cls, pix_area)
    tot = sum(areas.values())
    print("[3/4] 2026-07-17 areas (plain, after MMU): " +
          " | ".join(f"{k} {v:,.0f} km² ({100 * v / tot:.1f}%)" for k, v in areas.items()))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap

    fig, ax = plt.subplots(1, 3, figsize=(16, 5), constrained_layout=True)
    ax[0].hist(hv[plain], bins=200, range=(-35, -5), color="0.6", density=True, label="plain")
    ax[0].hist(hv[tiles], bins=200, range=(-35, -5), histtype="step", color="k", density=True, label="bimodal tiles")
    ax[0].axvline(t_hv, color="b"); ax[0].set_title(f"HV dB  (thr {t_hv:.2f})"); ax[0].legend()
    ax[1].hist(hh[plain], bins=200, range=(-30, 5), color="0.6", density=True)
    for t, c in [(t_hh_w, "b"), (t_hh_fv, "g")]:
        ax[1].axvline(t, color=c)
    ax[1].set_title(f"HH dB  (water < {t_hh_w:.2f}, fv > {t_hh_fv:.2f})")
    d = (hh - hv)[nonwater]
    ax[2].hist2d(hh[nonwater], d, bins=200, range=[[-20, 5], [0, 15]], cmap="magma", norm=matplotlib.colors.LogNorm())
    ax[2].axvline(t_hh_fv, color="lime"); ax[2].axhline(t_d_fv, color="lime")
    ax[2].set_xlabel("HH dB"); ax[2].set_ylabel("HH−HV dB"); ax[2].set_title("non-water plain")
    figdir = ROOT / "outputs/figures"
    fig.savefig(figdir / "calib_hist_20260717.png", dpi=110)
    plt.close(fig)

    rgbm = np.where(urban & valid, 4, np.where(high & valid, 5, cls))
    cmap = ListedColormap(["#ffffff", "#1f4e9c", "#2ca25f", "#e8dcc0", "#d62728", "#7f7f7f"])
    fig, ax = plt.subplots(1, 2, figsize=(14, 11), constrained_layout=True)
    ax[0].imshow(rgbm, cmap=cmap, vmin=0, vmax=5, interpolation="nearest")
    ax[0].set_title("2026-07-17 classes\nblue=open water  green=flooded veg  beige=land  red=urban  grey=>135 m",
                    fontsize=9)
    lo, hi = np.nanpercentile(hh, [2, 98])
    g = np.clip((hh - lo) / (hi - lo), 0, 1)
    ov = np.dstack([g, g, g])
    ov[~np.isfinite(hh)] = 1
    ov[cls == FLOODVEG] = [0.0, 0.9, 0.2]
    ov[cls == WATER] = [0.1, 0.3, 1.0]
    ov[perm_full & ~(cls == WATER)] = [1.0, 0.0, 1.0]   # JRC permanent water NOT classified as water
    ax[1].imshow(ov, interpolation="nearest")
    ax[1].set_title("HH background | green=flooded veg  blue=water\nmagenta=JRC permanent water missed", fontsize=9)
    for a in ax:
        a.set_axis_off()
    fig.savefig(figdir / "class_preview_20260717.png", dpi=110)
    plt.close(fig)
    print(f"      figures: {figdir}/calib_hist_20260717.png, class_preview_20260717.png")

    # ---------------------------------------------------------- Ladário
    print("[4/4] Ladário gauge:")
    daily, meta = load_ladario_daily(args.gauge)
    print(f"      time col='{meta['time_col']}' level col='{meta['level_col']}' "
          f"{meta['n_raw']} readings, {meta['n_spikes']} spikes removed, {meta['start']} → {meta['end']}")
    for dt in DATES:
        key = f"{dt[:4]}-{dt[4:6]}-{dt[6:]}"
        if key in daily.index.strftime("%Y-%m-%d"):
            row = daily.loc[key]
            print(f"      {key}: stage {row['stage']:.1f}  (n={int(row['n_obs'])})")
        else:
            print(f"      {key}: no data")


if __name__ == "__main__":
    main()
