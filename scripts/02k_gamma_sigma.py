# AI-assisted: written with Claude (Anthropic) from the author’s specifications; reviewed and run by the author. See docs/ai_use.md
"""Step 2k: measured sigma0 -> gamma0 offset from the GCOV layer rtcGammaToSigmaFactor (17 Jul), inside the floodplain.

The GCOV layer /science/LSAR/GCOV/grids/frequencyA/rtcGammaToSigmaFactor holds linear factors that convert the
GCOV terms from gamma0 to sigma0 (sigma0 = gamma0 * factor; ASF NISAR GCOV docs). We report the offset
gamma0 − sigma0 in dB = −10·log10(factor), which replaces the earlier assumption "+0.5 to 1.5 dB".

Floodplain = same mask as scripts/02b_calibrate.py: valid SAR, not urban (OSM), Copernicus DEM ≤ 135 m.
Factor is averaged (linear) from 20 m onto the 40 m analysis grid.

Rule fixed BEFORE running (same form as the old check, measured values instead of the assumption):
  accepted gamma0 range for a water threshold = [open-lake sigma0 + p2(offset), vegetated-lake sigma0 + p98(offset)]
  (Evans 2013 median sigma0, src/pantanal_sar/classify.py PHYS_REF). The script prints the check with the old
  assumed offsets and with the measured ones; if any flag changes it prints [CHECK CHANGED] -> stop and report.

Output: outputs/tables/gamma_sigma_factor.csv
Run: python scripts/02k_gamma_sigma.py [--h5 path/to/GCOV_20260717.h5]
"""
import argparse
import glob
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pantanal_sar.classify import (  # noqa: E402
    SIGMA0_TO_GAMMA0_ASSUMED, dem_on_grid, physical_check, ref_grid, urban_on_grid,
)
from pantanal_sar.gcov import find_freq_group, load_aoi, read_clip  # noqa: E402

LAYER = "rtcGammaToSigmaFactor"


def find_h5(date):
    c = [f for f in glob.glob(str(ROOT / f"data/**/*{date}*.h5"), recursive=True) if "gcov" in f.lower()]
    if not c:
        sys.exit(f"[ERROR] no GCOV .h5 for {date} under data/ (use --h5)")
    return sorted(c)[0]


def read_thresholds(path):
    th = {}
    for line in Path(path).read_text().splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, v = line.split(":", 1)
            th[k.strip()] = float(v)
    return th


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="20260717")
    ap.add_argument("--h5", default=None)
    ap.add_argument("--ref", default=str(ROOT / "data/processed/gcov_20260717_40m_db.tif"))
    ap.add_argument("--aoi", default=str(ROOT / "config/aoi.geojson"))
    ap.add_argument("--dem-dir", default=str(ROOT / "data/external/dem"))
    ap.add_argument("--urban-dir", default=str(ROOT / "data/external/urban_mask"))
    ap.add_argument("--max-height", type=float, default=135.0)
    args = ap.parse_args()

    h5 = args.h5 or find_h5(args.date)
    print(f"[1/4] GCOV: {Path(h5).name}")
    with h5py.File(h5, "r") as f:
        g = f[find_freq_group(f)]
        if LAYER not in g:
            hits = []
            f.visit(lambda n: hits.append(n) if "sigma" in n.lower() else None)
            sys.exit(f"[ERROR] {LAYER} not in {g.name}. Datasets with 'sigma' in the name: {hits[:10]}")
        print(f"      {g.name}/{LAYER}: shape {g[LAYER].shape}, dtype {g[LAYER].dtype} "
              f"(HHHH shape {g['HHHH'].shape})")
        if g[LAYER].shape != g["HHHH"].shape:
            sys.exit("[ERROR] factor layer is not on the HHHH grid; not handled -> report before continuing")

    clip = read_clip(h5, load_aoi(args.aoi), pols=("HHHH", LAYER))
    fac20 = np.where(np.isfinite(clip.bands["HHHH"]), clip.bands[LAYER], np.nan).astype("float32")

    grid = ref_grid(args.ref)
    fac40 = np.full(grid["shape"], np.nan, dtype="float32")
    reproject(fac20, fac40, src_transform=clip.transform, src_crs=f"EPSG:{clip.epsg}",
              dst_transform=grid["transform"], dst_crs=grid["crs"], resampling=Resampling.average,
              src_nodata=np.nan, dst_nodata=np.nan)

    with rasterio.open(args.ref) as r:
        valid = np.isfinite(r.read(1)) & np.isfinite(r.read(2))
    dem, _ = dem_on_grid(args.dem_dir, grid)
    urban, _ = urban_on_grid(args.urban_dir, grid)
    plain = valid & ~urban & np.isfinite(dem) & (dem <= args.max_height)
    v = fac40[plain & np.isfinite(fac40) & (fac40 > 0)]
    print(f"[2/4] floodplain pixels with a factor: {v.size:,} of {plain.sum():,} (40 m)")
    if v.size == 0:
        sys.exit("[ERROR] no factor values inside the floodplain")

    off = -10 * np.log10(v)                                   # gamma0 − sigma0 (dB)
    p2, p50, p98 = np.percentile(off, [2, 50, 98])
    fmed = float(np.median(v))
    inc = float(np.degrees(np.arccos(np.clip(fmed, -1, 1)))) if fmed <= 1 else float("nan")
    print(f"[3/4] factor (linear) median {fmed:.3f}  ->  gamma0 − sigma0 = {p50:+.2f} dB "
          f"(p2–p98 {p2:+.2f} to {p98:+.2f}; min–max {off.min():+.2f} to {off.max():+.2f})")
    print(f"      flat-terrain reading: factor = cos(incidence) -> median incidence ≈ {inc:.1f}°")
    if fmed >= 1:
        print("[ALERT] median factor ≥ 1 (sigma0 ≥ gamma0): unexpected on flat terrain -> check the convention, "
              "do NOT publish; report before continuing")

    out = pd.DataFrame([dict(date=args.date, layer=LAYER, file=Path(h5).name, n_px=int(v.size),
                             factor_median=fmed, offset_median_db=p50, offset_p2_db=p2, offset_p98_db=p98,
                             offset_min_db=float(off.min()), offset_max_db=float(off.max()),
                             incidence_median_deg=inc)])
    (ROOT / "outputs/tables").mkdir(parents=True, exist_ok=True)
    out.to_csv(ROOT / "outputs/tables/gamma_sigma_factor.csv", index=False, float_format="%.4f")
    print("      saved outputs/tables/gamma_sigma_factor.csv")

    th = read_thresholds(ROOT / "config/thresholds.yaml")
    old = physical_check(th, offsets=SIGMA0_TO_GAMMA0_ASSUMED)
    new = physical_check(th, offsets=(p2, p98))
    print("[4/4] physical check vs Evans (2013): assumed +0.5..+1.5 dB  vs  measured p2..p98")
    changed = False
    for (k, val, r_old, f_old, _), (_, _, r_new, f_new, _) in zip(old, new):
        print(f"      {k:16} {val:7.2f} dB | assumed {r_old:16} {f_old:12} | measured {r_new:16} {f_new}")
        changed |= f_old != f_new
    print("[CHECK CHANGED] stop and report before running 99_finalize.sh" if changed
          else "[CHECK UNCHANGED] flags are the same with the measured offset")


if __name__ == "__main__":
    main()
