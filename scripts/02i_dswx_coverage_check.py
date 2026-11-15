#!/usr/bin/env python
# AI-assisted: written with Claude (Anthropic) from the author’s specifications; reviewed and run by the author. See docs/ai_use.md
"""Step 2i (audit): independent per-file check of DSWx-HLS coverage on a given date (default 2 Sep).

For every DSWx file of that date, in its OWN grid (no mosaic, no reprojection of the data):
valid (0/1/2), cloud (252/253) and fill (254/255) km² inside the study area.
Then compares with the mosaic used by the pipeline (02e mosaic on the 40 m grid), on the same study area.
If one single file already covers much more than the mosaic says, the mosaic is wrong -> [ALERT].
Writes outputs/tables/dswx_coverage_files.csv.  Run from the repo root:  python scripts/02i_dswx_coverage_check.py
"""
from __future__ import annotations

import argparse
import glob
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import mapping, shape
from shapely.ops import transform as shp_transform
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="20260902")
    args = ap.parse_args()
    gj = json.loads((ROOT / "config/aoi.geojson").read_text())
    geom = gj["features"][0]["geometry"] if gj.get("type") == "FeatureCollection" else gj.get("geometry", gj)
    aoi = shape(geom)
    files = sorted(glob.glob(str(ROOT / f"data/raw/opera_dswx/*_{args.date}T*_B01_WTR.tif")))
    rows = []
    for f in files:
        p = Path(f).name.split("_")
        with rasterio.open(f) as s:
            a = s.read(1)
            tr = Transformer.from_crs(4326, s.crs, always_xy=True)
            aoi_f = shp_transform(tr.transform, aoi.segmentize(0.01))
            inside = geometry_mask([mapping(aoi_f)], out_shape=a.shape, transform=s.transform, invert=True)
            px = abs(s.transform.a * s.transform.e) / 1e6
        rows.append(dict(file=Path(f).name, tile=p[3], sensor=p[6], time=p[4],
                         aoi_km2_in_tile=inside.sum() * px,
                         valid_km2=(inside & np.isin(a, (0, 1, 2))).sum() * px,
                         cloud_km2=(inside & np.isin(a, (252, 253))).sum() * px,
                         fill_km2=(inside & np.isin(a, (254, 255))).sum() * px,
                         file_valid_pct=100 * np.isin(a, (0, 1, 2)).mean(),
                         file_fill_pct=100 * np.isin(a, (254, 255)).mean()))
    df = pd.DataFrame(rows)

    # mosaic on the same study area (40 m grid) for comparison
    spec = importlib.util.spec_from_file_location("dswx", ROOT / "scripts/02e_dswx_compare.py")
    dswx = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dswx)
    ref = sorted(glob.glob(str(ROOT / "data/processed/gcov_*_40m_db.tif")))[0]
    with rasterio.open(ref) as r:
        grid = dict(transform=r.transform, crs=r.crs, shape=r.shape)
        px40 = abs(r.transform.a * r.transform.e) / 1e6
        tr = Transformer.from_crs(4326, r.crs, always_xy=True)
        inside40 = geometry_mask([mapping(shp_transform(tr.transform, aoi.segmentize(0.01)))],
                                 out_shape=r.shape, transform=r.transform, invert=True)
    m = dswx.mosaic(files, grid)
    aoi_km2 = inside40.sum() * px40
    mos_valid = (inside40 & np.isin(m, (0, 1, 2))).sum() * px40
    mos_cloud = (inside40 & np.isin(m, (252, 253))).sum() * px40

    with pd.option_context("display.width", 220, "display.max_columns", 20):
        print(df.drop(columns=["file"]).round(1).to_string(index=False))
    best = df["valid_km2"].max() if len(df) else 0
    print(f"\nStudy area: {aoi_km2:,.0f} km²")
    print(f"Mosaic (pipeline): valid {mos_valid:,.0f} km² ({100 * mos_valid / aoi_km2:.1f}%), "
          f"cloud {mos_cloud:,.0f} km², rest not imaged")
    print(f"Largest single-file valid area: {best:,.0f} km² ({100 * best / aoi_km2:.1f}%); "
          f"sum over files (upper bound, overlaps double-counted): {df['valid_km2'].sum():,.0f} km²")
    if best > mos_valid * 1.05 + 1:
        print("[ALERT] a single file covers more than the mosaic -> mosaic bug, do NOT publish the coverage claim")
    else:
        print("[OK] per-file areas are consistent with the mosaic")
    df.to_csv(ROOT / "outputs/tables/dswx_coverage_files.csv", index=False, float_format="%.2f")


if __name__ == "__main__":
    main()
