#!/usr/bin/env python
"""Step 3a: export web assets (Leaflet overlays in EPSG:3857 + data.json) into web/.

Overlays (PNG with transparency, bounds in lat/lon):
  composite_<date>.png  R=HH G=HV B=HH-HV, same stretch for all dates, stable-reference offset removed
  classes_<date>.png    NISAR open water (blue) / flooded veg (green); land transparent
  change.png            17 Jul -> 21 Oct (water both / lost / gained)
  hydroperiod.png       number of dates as open water (1..8)
data.json: series (NISAR, DSWx, Ladário), headline metrics, all read from outputs/tables.
Run from the repo root:  python scripts/03_export_web.py
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from PIL import Image
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject, transform_bounds
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
BEFORE, AFTER = "20260717", "20261021"
SEP_N, SEP_D = "20260903", "20260902"      # radar vs optical in the fire season
DST = CRS.from_epsg(3857)


def to_3857(rgba, src_transform, src_crs, resampling):
    h, w = rgba.shape[:2]
    left, top = src_transform.c, src_transform.f
    right, bottom = left + w * src_transform.a, top + h * src_transform.e
    tr, W, H = calculate_default_transform(src_crs, DST, w, h, left, bottom, right, top)
    out = np.zeros((4, H, W), dtype="uint8")
    for b in range(4):
        reproject(rgba[..., b], out[b], src_transform=src_transform, src_crs=src_crs,
                  dst_transform=tr, dst_crs=DST, resampling=resampling, src_nodata=None)
    b3857 = (tr.c, tr.f + H * tr.e, tr.c + W * tr.a, tr.f)
    w_, s_, e_, n_ = transform_bounds(DST, "EPSG:4326", *b3857)
    return np.moveaxis(out, 0, -1), [[s_, w_], [n_, e_]]


def save(name, rgba, src_transform, src_crs, layers, resampling=Resampling.nearest, webp=False):
    img, bounds = to_3857(rgba, src_transform, src_crs, resampling)
    (WEB / "img").mkdir(parents=True, exist_ok=True)
    fn = f"{name}.webp" if webp else f"{name}.png"
    im = Image.fromarray(img, "RGBA")
    if webp:
        im.save(WEB / "img" / fn, "WEBP", quality=80, method=6)
    else:
        im.save(WEB / "img" / fn, optimize=True)
    layers[name] = {"url": f"img/{fn}", "bounds": bounds}
    print(f"      img/{fn}  {img.shape[1]}x{img.shape[0]}  {(WEB / 'img' / fn).stat().st_size / 1e6:.1f} MB")


def palette_rgba(arr, colors, alpha_zero=()):
    out = np.zeros(arr.shape + (4,), dtype="uint8")
    for k, (r, g, b, a) in colors.items():
        out[arr == k] = (r, g, b, a)
    return out


def main():
    proc, tabs = ROOT / "data/processed", ROOT / "outputs/tables"
    stab = pd.read_csv(tabs / "stability.csv", dtype={"date": str}).set_index("date")
    layers = {}
    print("[1/3] overlays")

    # --- composites with a common stretch (from BEFORE, after offset removal)
    def load(d):
        with rasterio.open(proc / f"gcov_{d}_40m_db.tif") as r:
            hh, hv = r.read(1), r.read(2)
            return hh - stab.loc[d, "d_hh_stable"], hv - stab.loc[d, "d_hv_stable"], r.transform, r.crs

    hh0, hv0, tr, crs = load(BEFORE)
    lim = {"hh": np.nanpercentile(hh0, [2, 98]), "hv": np.nanpercentile(hv0, [2, 98]),
           "df": np.nanpercentile(hh0 - hv0, [2, 98])}
    for d in (BEFORE, AFTER, SEP_N):
        hh, hv, tr, crs = load(d)
        ok = np.isfinite(hh) & np.isfinite(hv)
        chans = []
        for a, k in ((hh, "hh"), (hv, "hv"), (hh - hv, "df")):
            lo, hi = lim[k]
            chans.append(np.nan_to_num(np.clip((a - lo) / (hi - lo) * 255, 0, 255)))
        rgba = np.dstack(chans + [np.where(ok, 255, 0)]).astype("uint8")
        rgba[~ok] = 0
        save(f"composite_{d}", rgba, tr, crs, layers, Resampling.bilinear, webp=True)

    # --- DSWx-HLS 2 Sep (cloudy) on the NISAR 3 Sep footprint
    import importlib.util
    spec = importlib.util.spec_from_file_location("dswx", ROOT / "scripts/02e_dswx_compare.py")
    dswx = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dswx)
    grid = dict(transform=tr, crs=crs, shape=hh0.shape)
    w = dswx.mosaic(sorted(glob.glob(str(ROOT / f"data/raw/opera_dswx/*_{SEP_D}T*_B01_WTR.tif"))), grid)
    hh3, _, _, _ = load(SEP_N)
    w[~np.isfinite(hh3)] = 255
    save(f"dswx_{SEP_D}", palette_rgba(w, {0: (226, 214, 180, 255), 1: (31, 78, 156, 255),
                                         2: (120, 180, 230, 255), 253: (250, 250, 250, 255),
                                         252: (250, 250, 250, 255)}), tr, crs, layers)

    # --- classes
    for d in (BEFORE, AFTER):
        with rasterio.open(proc / f"class_{d}.tif") as r:
            c, tr, crs = r.read(1), r.transform, r.crs
        save(f"classes_{d}", palette_rgba(c, {1: (31, 78, 156, 255), 2: (44, 162, 95, 255)}), tr, crs, layers)

    # --- change & hydroperiod
    with rasterio.open(ROOT / f"outputs/maps/change_{BEFORE}_{AFTER}.tif") as r:
        c, tr, crs = r.read(1), r.transform, r.crs
    save("change", palette_rgba(c, {1: (31, 78, 156, 255), 2: (230, 85, 13, 255), 3: (107, 174, 214, 255),
                                    4: (253, 174, 107, 255), 5: (116, 196, 118, 255), 6: (35, 139, 69, 255)}),
         tr, crs, layers)
    with rasterio.open(ROOT / "outputs/maps/hydroperiod.tif") as r:
        h, tr, crs = r.read(1), r.transform, r.crs
    import matplotlib
    cmap = matplotlib.colormaps["Blues"]
    n = int(h[h != 255].max())
    cols = {k: tuple(int(255 * v) for v in cmap(0.25 + 0.75 * k / n)[:3]) + (255,) for k in range(1, n + 1)}
    save("hydroperiod", palette_rgba(h, cols), tr, crs, layers)

    # --- data.json
    print("[2/3] data.json")
    area = pd.read_csv(tabs / "area_series.csv")
    comp = pd.read_csv(tabs / "dswx_comparison.csv", dtype={"nisar_date": str, "dswx_date": str})
    agr = pd.read_csv(tabs / "dswx_agreement_all_pairs.csv", dtype={"nisar_date": str, "dswx_date": str})
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from pantanal_sar.classify import load_ladario_daily
    daily, _ = load_ladario_daily(ROOT / "data/external/ladario_gauge/ladario_stage_raw_telemetria.csv",
                                  verbose=False)
    t0 = pd.Timestamp(area["date"].iloc[0]) - pd.Timedelta(days=20)
    t1 = pd.Timestamp(area["date"].iloc[-1]) + pd.Timedelta(days=15)
    st = daily.loc[t0:t1, "stage"].dropna()

    def ymd(s):
        return f"{s[:4]}-{s[4:6]}-{s[6:]}" if "-" not in s else s

    r_par, p_par = stats.pearsonr(comp["stage_at_dswx_cm"], comp["series_dswx_open_partial_km2"])
    r_op, p_op = stats.pearsonr(comp["stage_at_dswx_cm"], comp["series_dswx_open_km2"])
    cloudy = agr.sort_values("clear_pct").iloc[0]
    data = {
        "nisar": [{"date": str(d), "water_km2": round(w, 1)} for d, w in zip(area["date"], area["water_km2"])],
        "dswx_common": [{"date": ymd(d), "open_km2": round(o, 1), "open_partial_km2": round(op, 1),
                         "nisar_km2": round(nk, 1)}
                        for d, o, op, nk in zip(comp["dswx_date"], comp["series_dswx_open_km2"],
                                                comp["series_dswx_open_partial_km2"], comp["series_nisar_km2"])],
        "stage": [{"date": str(i.date()), "cm": round(v, 1)} for i, v in st.items()],
        "metrics": {
            "precision": [round(agr["precision"].min(), 2), round(agr["precision"].max(), 2)],
            "recall": [round(agr["recall"].min(), 2), round(agr["recall"].max(), 2)],
            "iou": [round(agr["iou"].min(), 2), round(agr["iou"].max(), 2)],
            "n_pairs": int(len(agr)),
            "nisar_dswx_ratio": round(float((comp["series_nisar_km2"] / comp["series_dswx_open_km2"]).mean()), 2),
            "r_open": round(r_op, 2), "p_open": round(p_op, 3),
            "r_open_partial": round(r_par, 2), "p_open_partial": round(p_par, 3),
            "common_km2": None,
            "open_first": round(comp["series_dswx_open_km2"].iloc[0]),
            "open_last": round(comp["series_dswx_open_km2"].iloc[-1]),
            "op_first": round(comp["series_dswx_open_partial_km2"].iloc[0]),
            "op_last": round(comp["series_dswx_open_partial_km2"].iloc[-1]),
            "stage_first": round(comp["stage_at_dswx_cm"].iloc[0]),
            "stage_last": round(comp["stage_at_dswx_cm"].iloc[-1]),
            "cloudy_dswx_date": ymd(cloudy["dswx_date"]), "cloudy_clear_pct": round(cloudy["clear_pct"]),
            "cloudy_nisar_date": ymd(cloudy["nisar_date"]),
            "sep_clear_pct": round(float(agr.loc[agr["dswx_date"] == SEP_D, "clear_pct"].iloc[0])),
        },
        "before": ymd(BEFORE), "after": ymd(AFTER), "sep_nisar": ymd(SEP_N), "sep_dswx": ymd(SEP_D),
    }
    for name, key in (("jul_aug_loss.csv", "jul_aug_loss"), ("partial_clf_summary.csv", "classifier"),
                      ("wind_check.csv", "wind")):
        f = tabs / name
        if f.exists():
            data[key] = json.loads(pd.read_csv(f).iloc[0].to_json())
    (WEB / "data").mkdir(parents=True, exist_ok=True)
    (WEB / "data" / "data.json").write_text(json.dumps(data, indent=1))
    (WEB / "data" / "layers.json").write_text(json.dumps(layers, indent=1))
    print(f"      web/data/data.json, web/data/layers.json")
    print("[3/3] preview locally:  python -m http.server -d web 8000   ->  http://localhost:8000")


if __name__ == "__main__":
    main()
