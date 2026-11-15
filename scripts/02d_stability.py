#!/usr/bin/env python
"""Step 2d: is the water-area series driven by scene brightness? Stable-zone diagnostic.

1) Per-date median HH/HV in a STABLE zone (hills, DEM > 200 m: forest that never floods)
   vs the plain -> offsets relative to the reference date.
2) Threshold sensitivity: water area with thresholds shifted -1 / 0 / +1 dB.
3) Normalised series: thresholds shifted per date by the stable-zone offset -> area vs Ladário.
Writes outputs/tables/stability.csv. Run from the repo root:  python scripts/02d_stability.py
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pantanal_sar.classify import WATER, classify, load_ladario_daily, remove_small  # noqa: E402

STABLE_MIN_M = 200.0
REF = "20260717"


def read_thresholds(path):
    th = {}
    for line in Path(path).read_text().splitlines():
        line = line.split("#")[0].strip()
        if ":" in line:
            k, v = line.split(":", 1)
            th[k.strip()] = float(v)
    return th


def main():
    proc = ROOT / "data/processed"
    th = read_thresholds(ROOT / "config/thresholds.yaml")
    min_px = int(th["mmu_px"])
    files = sorted(glob.glob(str(proc / "gcov_*_40m_db.tif")))
    dates = [Path(f).name.split("_")[1] for f in files]

    with rasterio.open(proc / "masks_40m.tif") as m:
        urban, high, dem = m.read(1), m.read(2), m.read(3)
        pix_area = abs(m.transform.a * m.transform.e)
    plain = (urban == 0) & (high == 0) & np.isfinite(dem)
    stable = (urban == 0) & np.isfinite(dem) & (dem > STABLE_MIN_M)

    data = {}
    for d, f in zip(dates, files):
        with rasterio.open(f) as r:
            data[d] = (r.read(1), r.read(2))
    common = np.logical_and.reduce([np.isfinite(hh) & np.isfinite(hv) for hh, hv in data.values()])
    stable &= common
    plainc = plain & common
    print(f"[1/3] stable zone (DEM > {STABLE_MIN_M:.0f} m, valid all dates): "
          f"{stable.sum() * pix_area / 1e6:,.0f} km² | plain (common): {plainc.sum() * pix_area / 1e6:,.0f} km²")

    rows = []
    for d in dates:
        hh, hv = data[d]
        rows.append(dict(date=d,
                         hh_stable=np.median(hh[stable]), hv_stable=np.median(hv[stable]),
                         hh_plain=np.median(hh[plainc]), hv_plain=np.median(hv[plainc])))
    df = pd.DataFrame(rows).set_index("date")
    for c in ["hh_stable", "hv_stable", "hh_plain", "hv_plain"]:
        df[f"d_{c}"] = df[c] - df.loc[REF, c]

    def water_area(d, dhh=0.0, dhv=0.0):
        t = dict(th)
        t["water_hh_max"] += dhh
        t["water_hv_max"] += dhv
        t["floodveg_hh_min"] += dhh
        hh, hv = data[d]
        cls = remove_small(classify(hh, hv, t, plainc), min_px)
        return (cls == WATER).sum() * pix_area / 1e6

    print("[2/3] water area (km²) with thresholds shifted by -1 / 0 / +1 dB, and stable-normalised:")
    for d in dates:
        df.loc[d, "water_m1"] = water_area(d, -1, -1)
        df.loc[d, "water_0"] = water_area(d)
        df.loc[d, "water_p1"] = water_area(d, +1, +1)
        df.loc[d, "water_norm"] = water_area(d, df.loc[d, "d_hh_stable"], df.loc[d, "d_hv_stable"])

    daily, _ = load_ladario_daily(ROOT / "data/external/ladario_gauge/ladario_stage_raw_telemetria.csv",
                                  verbose=False)
    df["stage_cm"] = [daily["stage"].get(pd.Timestamp(f"{d[:4]}-{d[4:6]}-{d[6:]}"), np.nan) for d in dates]
    with pd.option_context("display.width", 220, "display.max_columns", 30):
        print(df[["hh_stable", "d_hh_stable", "d_hv_stable", "d_hh_plain", "d_hv_plain",
                  "water_m1", "water_0", "water_p1", "water_norm", "stage_cm"]].round(2).to_string())

    print("[3/3] diagnostics:")
    r, p = stats.pearsonr(df["d_hh_stable"], df["d_hh_plain"])
    print(f"      plain HH offset vs stable HH offset: r={r:.2f} (p={p:.3f})  "
          f"[high r -> scene-wide brightness change, not hydrology]")
    sens = (df["water_p1"] - df["water_m1"]).median() / 2
    print(f"      sensitivity: ~{sens:.0f} km² per 1 dB of threshold  "
          f"(date-to-date range of raw series: {df['water_0'].max() - df['water_0'].min():.0f} km²)")
    for col in ["water_0", "water_norm"]:
        rho, ps = stats.spearmanr(df["stage_cm"], df[col])
        r, pr = stats.pearsonr(df["stage_cm"], df[col])
        print(f"      {col:10} vs Ladário: Pearson r={r:.2f} (p={pr:.3f})  Spearman ρ={rho:.2f} (p={ps:.3f})")
    out = ROOT / "outputs/tables/stability.csv"
    df.to_csv(out, float_format="%.3f")
    print(f"      saved {out}")


if __name__ == "__main__":
    main()
