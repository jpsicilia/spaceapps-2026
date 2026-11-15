#!/usr/bin/env python
"""Step 1: NISAR GCOV -> AOI clip -> 40 m -> Lee -> dB GeoTIFF + quicklook.

Usage (from the repo root):
    python scripts/01_preprocess_gcov.py --date 20260717
    python scripts/01_preprocess_gcov.py --file data/raw/gcov/NISAR_..._20260717....h5
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pantanal_sar.gcov import (  # noqa: E402
    aoi_mask, estimate_enl, lee_filter, load_aoi, multilook, read_clip, to_db,
)


def find_gcov(data_dir: Path, date: str) -> Path:
    cands = [p for p in data_dir.rglob("*.h5") if date in p.name]
    gcov = [p for p in cands if "GCOV" in p.name.upper()]
    pick = gcov or cands
    if not pick:
        sys.exit(f"[ERROR] No .h5 with '{date}' in its name under {data_dir}. Use --file.")
    if len(pick) > 1:
        print(f"[WARN] {len(pick)} matches, using the first:\n  " + "\n  ".join(map(str, pick)))
    return pick[0]


def pct(a, q=(2, 50, 98)):
    v = a[np.isfinite(a)]
    return " / ".join(f"{np.percentile(v, x):6.2f}" for x in q) if v.size else "n/a"


def quicklook(hh_db, hv_db, out_png: Path, title: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def stretch(a):
        lo, hi = np.nanpercentile(a, [2, 98])
        return np.clip((a - lo) / (hi - lo), 0, 1)

    diff = hh_db - hv_db
    rgb = np.dstack([stretch(hh_db), stretch(hv_db), stretch(diff)])
    rgb[~np.isfinite(hh_db)] = 1.0

    fig, ax = plt.subplots(1, 3, figsize=(15, 9), constrained_layout=True)
    for a, img, t, cmap in [
        (ax[0], hh_db, "HH (dB)", "gray"),
        (ax[1], hv_db, "HV (dB)", "gray"),
    ]:
        lo, hi = np.nanpercentile(img, [2, 98])
        im = a.imshow(img, cmap=cmap, vmin=lo, vmax=hi)
        fig.colorbar(im, ax=a, shrink=0.6)
        a.set_title(t)
    ax[2].imshow(rgb)
    ax[2].set_title("R=HH  G=HV  B=HH−HV")
    for a in ax:
        a.set_axis_off()
    fig.suptitle(title)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=110)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="20260717", help="YYYYMMDD (dashes ok)")
    ap.add_argument("--file", type=Path, help="explicit GCOV .h5 path (overrides --date search)")
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data")
    ap.add_argument("--aoi", type=Path, default=ROOT / "config" / "aoi.geojson")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "data" / "processed")
    ap.add_argument("--fig-dir", type=Path, default=ROOT / "outputs" / "figures")
    ap.add_argument("--res", type=float, default=40.0, help="target pixel size (m)")
    ap.add_argument("--lee-size", type=int, default=5, help="Lee window (pixels at target res)")
    ap.add_argument("--enl", type=float, default=None, help="override ENL (default: estimated)")
    args = ap.parse_args()

    date = args.date.replace("-", "")
    h5 = args.file or find_gcov(args.data_dir, date)
    aoi = load_aoi(args.aoi)
    print(f"[1/5] File : {h5}")

    clip = read_clip(h5, aoi)
    f = max(1, int(round(args.res / clip.spacing)))
    print(f"[2/5] Group: {clip.meta['h5_group']} | EPSG:{clip.epsg} | native {clip.spacing:.2f} m"
          f" -> multilook {f}x{f} = {clip.spacing * f:.1f} m | native window {clip.bands['HHHH'].shape}")

    lin = {k: multilook(v, f) for k, v in clip.bands.items()}
    tr = clip.transform * Affine.scale(f, f)
    shape_ = lin["HHHH"].shape
    inside = aoi_mask(clip.meta["aoi_xy"], shape_, tr)

    nominal = None
    if clip.nlooks is not None:
        nl = multilook(clip.nlooks, f)
        nominal = float(np.nanmedian(nl)) * f * f
    enl = args.enl or estimate_enl(lin["HVHV"])
    nom_txt = f"{nominal:.1f}" if nominal else "n/a"
    print(f"[3/5] ENL  : nominal={nom_txt}  estimated={estimate_enl(lin['HVHV']):.2f}"
          f"  used={enl:.2f} | Lee {args.lee_size}x{args.lee_size}")

    filt = {k: lee_filter(v, args.lee_size, enl) for k, v in lin.items()}
    hh_db, hv_db = to_db(filt["HHHH"]), to_db(filt["HVHV"])
    for a in (hh_db, hv_db):
        a[~inside | ~np.isfinite(a)] = np.nan

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_tif = args.out_dir / f"gcov_{date}_{int(args.res)}m_db.tif"
    profile = dict(driver="GTiff", height=shape_[0], width=shape_[1], count=2, dtype="float32",
                   crs=f"EPSG:{clip.epsg}", transform=tr, nodata=np.nan, compress="deflate",
                   tiled=True, blockxsize=256, blockysize=256)
    with rasterio.open(out_tif, "w", **profile) as dst:
        dst.write(hh_db, 1)
        dst.write(hv_db, 2)
        dst.set_band_description(1, "HH_gamma0_dB")
        dst.set_band_description(2, "HV_gamma0_dB")
        dst.update_tags(date=date, source=Path(h5).name, multilook=f, enl=f"{enl:.2f}",
                        lee_size=args.lee_size, processing="clip>multilook>lee(linear)>dB")
    print(f"[4/5] Saved: {out_tif}  ({shape_[0]}x{shape_[1]} px)")

    valid = np.isfinite(hh_db) & inside
    print(f"      valid inside AOI: {100 * valid.sum() / inside.sum():.1f}%")
    print(f"      HH dB  p2/p50/p98: {pct(hh_db)}")
    print(f"      HV dB  p2/p50/p98: {pct(hv_db)}")
    print(f"      HH-HV  p2/p50/p98: {pct(hh_db - hv_db)}")

    png = args.fig_dir / f"quicklook_{date}.png"
    quicklook(hh_db, hv_db, png, f"NISAR GCOV {date} — {int(args.res)} m, Lee {args.lee_size}x{args.lee_size}")
    print(f"[5/5] Quicklook: {png}")


if __name__ == "__main__":
    main()
