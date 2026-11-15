#!/usr/bin/env python
"""Step 2f: wind check on known water. Median HH/HV per date inside the JRC occurrence > 90% zone.

Decision rule fixed BEFORE looking (Pablo, 15 Nov):
  "wind" if Aug (10 Aug, 22 Aug) HH is >= 1.0 dB brighter than 17 Jul in the JRC zone after removing the
  hills (stable) offset, AND the HH increase is larger than the HV increase (roughening hits co-pol more).
  Otherwise "unexplained" (and we note that the 19 Jul DSWx pair is the only Landsat-9 one).
Also reported: the same medians restricted to pixels DSWx calls open water on the paired date (cleaner zone).
Run from the repo root:  python scripts/02f_wind_check.py
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

REF, AUG = "20260717", ("20260810", "20260822")
MIN_DB = 1.0


def main():
    proc, tabs = ROOT / "data/processed", ROOT / "outputs/tables"
    with rasterio.open(proc / "masks_40m.tif") as m:
        urban, high, dem, perm = (m.read(i) for i in (1, 2, 3, 4))
        grid = dict(transform=m.transform, crs=m.crs, shape=m.shape)
    zone = (perm == 1) & (urban == 0)
    stab = pd.read_csv(tabs / "stability.csv", dtype={"date": str}).set_index("date")

    # DSWx open water on paired dates (optional, cleaner zone)
    dswx_open = {}
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("dswx", ROOT / "scripts/02e_dswx_compare.py")
        dswx = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dswx)
        comp = pd.read_csv(tabs / "dswx_agreement_all_pairs.csv", dtype={"nisar_date": str, "dswx_date": str})
        for nd, dd in zip(comp["nisar_date"], comp["dswx_date"]):
            fs = sorted(glob.glob(str(ROOT / f"data/raw/opera_dswx/*_{dd}T*_B01_WTR.tif")))
            if fs:
                dswx_open[nd] = (dswx.mosaic(fs, grid) == 1, dd)
    except Exception as e:  # keep the main check alive
        print(f"      [WARN] DSWx-restricted medians skipped: {e}")

    rows = []
    for f in sorted(glob.glob(str(proc / "gcov_*_40m_db.tif"))):
        d = Path(f).name.split("_")[1]
        with rasterio.open(f) as r:
            hh, hv = r.read(1), r.read(2)
        z = zone & np.isfinite(hh) & np.isfinite(hv)
        row = dict(date=d, n_px=int(z.sum()), hh_jrc=np.median(hh[z]), hv_jrc=np.median(hv[z]),
                   hh_hills=stab.loc[d, "d_hh_stable"], hv_hills=stab.loc[d, "d_hv_stable"])
        if d in dswx_open:
            zz = z & dswx_open[d][0]
            row.update(dswx_date=dswx_open[d][1], n_px_dswx=int(zz.sum()),
                       hh_jrc_dswx=np.median(hh[zz]) if zz.any() else np.nan,
                       hv_jrc_dswx=np.median(hv[zz]) if zz.any() else np.nan)
        rows.append(row)
    df = pd.DataFrame(rows).set_index("date")
    for p in ("hh", "hv"):
        df[f"d_{p}_jrc"] = df[f"{p}_jrc"] - df.loc[REF, f"{p}_jrc"]
        df[f"d_{p}_jrc_corr"] = df[f"d_{p}_jrc"] - df[f"{p}_hills"]
        if f"{p}_jrc_dswx" in df:
            df[f"d_{p}_jrc_dswx_corr"] = df[f"{p}_jrc_dswx"] - df.loc[REF, f"{p}_jrc_dswx"] - df[f"{p}_hills"]

    with pd.option_context("display.width", 220, "display.max_columns", 30):
        cols = [c for c in ["n_px", "hh_jrc", "hv_jrc", "d_hh_jrc", "d_hv_jrc", "d_hh_jrc_corr", "d_hv_jrc_corr",
                            "dswx_date", "n_px_dswx", "d_hh_jrc_dswx_corr", "d_hv_jrc_dswx_corr"] if c in df]
        print("[1/2] medians in JRC occurrence > 90% zone (dB); d_* relative to 17 Jul; *_corr = minus hills offset")
        print(df[cols].round(2).to_string())

    aug = df.loc[list(AUG)]
    dhh, dhv = aug["d_hh_jrc_corr"].mean(), aug["d_hv_jrc_corr"].mean()
    wind = (dhh >= MIN_DB) and (dhh > dhv)
    if wind:
        verdict = (f"in August the permanent-water zone is {dhh:+.1f} dB brighter in HH than on 17 July "
                   f"(HV {dhv:+.1f} dB), after removing the stable-reference offset — consistent with "
                   "wind-roughened water, which raises HH above the open-water threshold.")
    else:
        verdict = (f"HH in the permanent-water zone changed only {dhh:+.1f} dB (HV {dhv:+.1f} dB) between "
                   "17 July and August after removing the stable-reference offset, so wind does not explain it; "
                   "the drop remains unexplained. Note the 17 July NISAR scene is paired with the only "
                   "Landsat-9 DSWx-HLS product (19 July); all other pairs are Sentinel-2.")
    print(f"[2/2] rule: wind if mean Aug ΔHH_corr >= {MIN_DB} dB and ΔHH > ΔHV  ->  "
          f"ΔHH={dhh:+.2f}, ΔHV={dhv:+.2f}  =>  {'WIND' if wind else 'UNEXPLAINED'}")
    print(f"      README text: {verdict}")
    pd.DataFrame([dict(verdict=verdict, d_hh=dhh, d_hv=dhv, wind=wind)]).to_csv(tabs / "wind_check.csv", index=False)
    df.to_csv(tabs / "wind_check_by_date.csv", float_format="%.3f")


if __name__ == "__main__":
    main()
