#!/usr/bin/env python
"""Step 2h: where does the NISAR open-water loss 17 Jul -> 10 Aug fall in DSWx-HLS 19 Jul?

Hypothesis (Pablo): in July NISAR saw submerged grass (very dark HH) as water; as vegetation emerged, HH rose
and NISAR lost it. PRE-REGISTERED rule: if > 50% of the lost area (on DSWx-clear pixels) is DSWx "partial" (2)
on 19 Jul, the drop is treated as real and README point 3 changes.
Also: share of NISAR 17 Jul water on DSWx partial; enrichment vs the plain-wide partial share; what DSWx 8 Aug
says on the same lost pixels.
Run from the repo root (after 02c --normalize):  python scripts/02h_jul_aug_loss.py
"""
from __future__ import annotations

import glob
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
WATER, NODATA = 1, 0
JUL, AUG, D_JUL, D_AUG = "20260717", "20260810", "20260719", "20260808"
LBL = {0: "not water", 1: "open", 2: "partial", 253: "cloud", 255: "fill"}


def main():
    spec = importlib.util.spec_from_file_location("dswx", ROOT / "scripts/02e_dswx_compare.py")
    dswx = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dswx)
    proc, tabs = ROOT / "data/processed", ROOT / "outputs/tables"

    with rasterio.open(proc / f"class_{JUL}.tif") as r:
        cj = r.read(1)
        grid = dict(transform=r.transform, crs=r.crs, shape=r.shape)
        pix = abs(r.transform.a * r.transform.e) / 1e6
    with rasterio.open(proc / f"class_{AUG}.tif") as r:
        ca = r.read(1)
    wj = {d: dswx.mosaic(sorted(glob.glob(str(ROOT / f"data/raw/opera_dswx/*_{d}T*_B01_WTR.tif"))), grid)
          for d in (D_JUL, D_AUG)}

    valid = (cj != NODATA) & (ca != NODATA)
    lost = valid & (cj == WATER) & (ca != WATER)
    kept = valid & (cj == WATER) & (ca == WATER)
    w19 = wj[D_JUL]
    clear19 = np.isin(w19, (0, 1, 2))

    def share(mask, w, clear):
        m = mask & clear
        n = m.sum()
        return {LBL[k]: 100 * (m & (w == k)).sum() / n if n else np.nan for k in (0, 1, 2)}, n * pix

    s_lost, a_lost = share(lost, w19, clear19)
    s_kept, a_kept = share(kept, w19, clear19)
    s_wj, a_wj = share(valid & (cj == WATER), w19, clear19)
    s_plain, a_plain = share(valid, w19, clear19)

    print(f"[1/3] NISAR lost water 17 Jul -> 10 Aug: {lost.sum() * pix:.1f} km² "
          f"({a_lost:.1f} km² on DSWx-clear pixels of 19 Jul)")
    print("      DSWx 19 Jul class on those pixels (% of clear):")
    for name, s, a in [("LOST (water Jul, not Aug)", s_lost, a_lost), ("kept (water both)", s_kept, a_kept),
                       ("all NISAR water 17 Jul", s_wj, a_wj), ("whole plain (reference)", s_plain, a_plain)]:
        print(f"      {name:27} {a:8.1f} km² | not water {s['not water']:5.1f}% | open {s['open']:5.1f}% | "
              f"partial {s['partial']:5.1f}%")
    enrich = s_lost["partial"] / s_plain["partial"] if s_plain["partial"] else np.nan
    print(f"      partial enrichment on lost pixels vs plain: x{enrich:.1f}")

    # what happened in DSWx on the same lost pixels (19 Jul -> 8 Aug)
    w08 = wj[D_AUG]
    both = lost & clear19 & np.isin(w08, (0, 1, 2))
    ct = pd.crosstab(pd.Series(w19[both], name="DSWx 19 Jul").map(LBL),
                     pd.Series(w08[both], name="DSWx 8 Aug").map(LBL)) * pix
    print("[2/3] lost pixels, DSWx 19 Jul -> 8 Aug (km², pixels clear on both dates):")
    print(ct.round(1).to_string())

    supports = s_lost["partial"] > 50
    print(f"[3/3] PRE-REGISTERED: partial share of lost area = {s_lost['partial']:.1f}% (> 50%) -> "
          f"{'SUPPORTS hypothesis (drop is real)' if supports else 'does NOT support hypothesis'}")
    pd.DataFrame([dict(lost_km2=lost.sum() * pix, lost_clear_km2=a_lost,
                       lost_partial_pct=s_lost["partial"], lost_open_pct=s_lost["open"],
                       lost_notwater_pct=s_lost["not water"], jul_water_on_partial_pct=s_wj["partial"],
                       plain_partial_pct=s_plain["partial"], enrichment=enrich, supports=supports)]
                 ).to_csv(tabs / "jul_aug_loss.csv", index=False, float_format="%.2f")
    ct.to_csv(tabs / "jul_aug_loss_dswx_transitions.csv", float_format="%.2f")


if __name__ == "__main__":
    main()
