# AI-assisted: written with Claude (Anthropic) from the author’s specifications; reviewed and run by the author. See docs/ai_use.md
"""Masks, threshold calibration and 3-class classification (open water / flooded vegetation / land)."""
from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.warp import reproject
from scipy import ndimage

# class codes
NODATA, WATER, FLOODVEG, LAND = 0, 1, 2, 3
CLASS_NAMES = {WATER: "open_water", FLOODVEG: "flooded_vegetation", LAND: "land"}

VECTOR_EXT = (".gpkg", ".geojson", ".json", ".shp", ".fgb")
RASTER_EXT = (".tif", ".tiff", ".vrt", ".hgt", ".img")


def _files(folder, exts):
    out = []
    for e in exts:
        out += glob.glob(str(Path(folder) / "**" / f"*{e}"), recursive=True)
    return sorted(out)


# ----------------------------------------------------------------- reference grid
def ref_grid(tif):
    with rasterio.open(tif) as r:
        return dict(transform=r.transform, crs=r.crs, shape=r.shape)


def warp_to_grid(src_path, grid, resampling=Resampling.bilinear, band=1, valid_max=None):
    """Reproject a raster onto the grid, reading only the window that covers it."""
    from rasterio.transform import array_bounds
    from rasterio.warp import transform_bounds
    from rasterio.windows import Window, from_bounds

    dst = np.full(grid["shape"], np.nan, dtype="float32")
    H, W = grid["shape"]
    left, bottom, right, top = array_bounds(H, W, grid["transform"])  # west, south, east, north
    with rasterio.open(src_path) as s:
        sb = transform_bounds(grid["crs"], s.crs, left, bottom, right, top, densify_pts=21)
        win = from_bounds(*sb, transform=s.transform).round_offsets().round_lengths()
        win = Window(win.col_off - 4, win.row_off - 4, win.width + 8, win.height + 8)
        win = win.intersection(Window(0, 0, s.width, s.height))
        src = s.read(band, window=win).astype("float32")
        src_tr = s.window_transform(win)
        if s.nodata is not None:
            src[src == s.nodata] = np.nan
        if valid_max is not None:
            src[src > valid_max] = np.nan
        reproject(src, dst, src_transform=src_tr, src_crs=s.crs,
                  dst_transform=grid["transform"], dst_crs=grid["crs"],
                  src_nodata=np.nan, dst_nodata=np.nan, resampling=resampling)
    return dst


# ---------------------------------------------------------------------- masks
def dem_on_grid(dem_dir, grid):
    """Mosaic all DEM tiles onto the grid (first valid value wins)."""
    files = _files(dem_dir, RASTER_EXT)
    if not files:
        raise FileNotFoundError(f"No DEM raster in {dem_dir}")
    out = np.full(grid["shape"], np.nan, dtype="float32")
    for f in files:
        a = warp_to_grid(f, grid, Resampling.bilinear)
        fill = np.isnan(out) & np.isfinite(a)
        out[fill] = a[fill]
    return out, files


def urban_on_grid(urban_dir, grid):
    """True = urban. Accepts OSM polygons (vector) or a raster mask (>0 = urban)."""
    vec = _files(urban_dir, VECTOR_EXT)
    if vec:
        import geopandas as gpd
        geoms = []
        for f in vec:
            g = gpd.read_file(f)
            g = g[g.geometry.notna()]
            g = g[g.geom_type.isin(["Polygon", "MultiPolygon"])]
            if len(g):
                geoms += list(g.to_crs(grid["crs"]).geometry)
        if not geoms:
            raise ValueError(f"No polygons found in {vec}")
        m = rasterize(((geom, 1) for geom in geoms), out_shape=grid["shape"],
                      transform=grid["transform"], fill=0, all_touched=True, dtype="uint8")
        return m.astype(bool), vec
    ras = _files(urban_dir, RASTER_EXT)
    if ras:
        a = warp_to_grid(ras[0], grid, Resampling.nearest)
        return np.nan_to_num(a) > 0, ras[:1]
    raise FileNotFoundError(f"No vector or raster urban mask in {urban_dir}")


def jrc_permanent_on_grid(jrc_dir, grid, occ_min=90.0, erode_px=1):
    """Permanent-water control zone: JRC GSW occurrence > occ_min (%).

    Resampling.min -> a 40 m pixel qualifies only if all its 30 m source pixels do;
    1-px erosion keeps the zone off mixed shoreline pixels.
    """
    files = [f for f in _files(jrc_dir, RASTER_EXT) if "occurrence" in Path(f).name.lower()]
    if not files:
        raise FileNotFoundError(f"No JRC occurrence raster in {jrc_dir}")
    occ = np.full(grid["shape"], np.nan, dtype="float32")
    for f in files:
        a = warp_to_grid(f, grid, Resampling.min, valid_max=100)
        fill = np.isnan(occ) & np.isfinite(a)
        occ[fill] = a[fill]
    perm = np.nan_to_num(occ) > occ_min
    if erode_px:
        perm = ndimage.binary_erosion(perm, iterations=erode_px)
    return perm, files


def control_water_pct(cls, perm):
    """% of the permanent-water control zone classified as open water."""
    z = perm & (cls != NODATA)
    return float(100 * np.mean(cls[z] == WATER)) if z.any() else float("nan")


# Physical sanity check against Evans (2013), MSc thesis, Univ. of Victoria, ch. 2 (Lower Nhecolândia), pp. 52-53,
# median ALOS PALSAR sigma0: brackish lakes without vegetation (salinas) HH -23 / HV -30 dB (HV dry season);
# fresh-water lakes with floating and emergent vegetation (baias) HH -14 / HV -23 dB.
# sigma0 -> gamma0 offset: MEASURED from the GCOV layer rtcGammaToSigmaFactor on 17 Jul inside the floodplain
# (scripts/02k_gamma_sigma.py -> outputs/tables/gamma_sigma_factor.csv, p2..p98 of gamma0 − sigma0 in dB).
# The earlier assumption (+0.5..+1.5 dB) is kept only as a fallback if that table is missing, and is labelled as such.
# A water threshold should lie between the open-lake and the vegetated-lake value (gamma0-adjusted).
SIGMA0_TO_GAMMA0_ASSUMED = (0.5, 1.5)
GAMMA_SIGMA_CSV = Path(__file__).resolve().parents[2] / "outputs/tables/gamma_sigma_factor.csv"


def sigma0_to_gamma0():
    """(low, high, source) offset gamma0 − sigma0 in dB: measured p2..p98 if available, else the old assumption."""
    if GAMMA_SIGMA_CSV.exists():
        import pandas as pd
        r = pd.read_csv(GAMMA_SIGMA_CSV).iloc[0]
        return float(r.offset_p2_db), float(r.offset_p98_db), "measured (rtcGammaToSigmaFactor, p2–p98)"
    return (*SIGMA0_TO_GAMMA0_ASSUMED, "ASSUMED (+0.5..+1.5 dB; run scripts/02k_gamma_sigma.py)")
PHYS_REF = [
    # key, open-lake sigma0, vegetated-lake sigma0, note, verified
    ("water_hh_max", -23.0, -14.0, "HH: salinas -23 dB, baias -14 dB (Evans 2013, median sigma0)", True),
    ("water_hv_max", -30.0, -23.0, "HV: salinas -30 dB, baias -23 dB (Evans 2013, median sigma0)", True),
    ("floodveg_hh_min", None, None, "flooded vegetation: no verified reference value", False),
]


def physical_check(th, offsets=None):
    rows = []
    lo_off, hi_off = offsets if offsets is not None else sigma0_to_gamma0()[:2]
    for key, s_open, s_veg, note, verified in PHYS_REF:
        v = th[key]
        if not verified:
            rows.append((key, v, "—", "NOT VERIFIED", note))
            continue
        lo, hi = s_open + lo_off, s_veg + hi_off
        ok = lo <= v <= hi
        rows.append((key, v, f"[{lo:+.1f}, {hi:+.1f}] γ0", "OK" if ok else "FAR", note))
    return rows


# ----------------------------------------------------------------- thresholds
def otsu(values, bins=256):
    v = values[np.isfinite(values)]
    hist, edges = np.histogram(v, bins=bins)
    c = (edges[:-1] + edges[1:]) / 2
    w0 = np.cumsum(hist)
    w1 = w0[-1] - w0
    m0 = np.cumsum(hist * c) / np.maximum(w0, 1)
    m1 = (np.sum(hist * c) - np.cumsum(hist * c)) / np.maximum(w1, 1)
    between = w0 * w1 * (m0 - m1) ** 2
    return float(c[np.argmax(between[:-1])])


def bimodal_tiles(img, valid, tile=50, top_q=90):
    """Split-based selection (Martinis-style): tiles with high std and below-global mean.

    Returns a boolean mask of the selected tiles' pixels and the number of tiles selected.
    """
    H, W = img.shape
    gmean = np.nanmean(img[valid])
    stats = []
    for r in range(0, H - tile + 1, tile):
        for c in range(0, W - tile + 1, tile):
            v = valid[r:r + tile, c:c + tile]
            if v.mean() < 0.9:
                continue
            x = img[r:r + tile, c:c + tile][v]
            stats.append((r, c, x.mean(), x.std()))
    if not stats:
        return valid.copy(), 0
    s = np.array(stats)
    std_thr = np.percentile(s[:, 3], top_q)
    sel = s[(s[:, 3] >= std_thr) & (s[:, 2] < gmean)]
    mask = np.zeros_like(valid)
    for r, c, _, _ in sel:
        r, c = int(r), int(c)
        mask[r:r + tile, c:c + tile] = valid[r:r + tile, c:c + tile]
    return mask, len(sel)


def robust_upper(x, k=2.0):
    """median + k * sigma_MAD."""
    x = x[np.isfinite(x)]
    med = np.median(x)
    sig = 1.4826 * np.median(np.abs(x - med))
    return float(med + k * sig), float(med), float(sig)


# ------------------------------------------------------------- classification
def classify(hh, hv, th, analysis_mask):
    """Fixed-threshold rule. analysis_mask = True where we classify (plain, non-urban, valid)."""
    diff = hh - hv
    cls = np.full(hh.shape, NODATA, dtype="uint8")
    ok = analysis_mask & np.isfinite(hh) & np.isfinite(hv)
    water = ok & (hv < th["water_hv_max"]) & (hh < th["water_hh_max"])
    fveg = ok & ~water & (hh > th["floodveg_hh_min"]) & (diff > th["floodveg_diff_min"])
    cls[ok] = LAND
    cls[fveg] = FLOODVEG
    cls[water] = WATER
    return cls


def remove_small(cls, min_px, classes=(WATER, FLOODVEG), fill=LAND):
    """Remove connected patches (8-connectivity) smaller than min_px; they become `fill`."""
    out = cls.copy()
    st = np.ones((3, 3), dtype=bool)
    for k in classes:
        lab, n = ndimage.label(cls == k, structure=st)
        if n == 0:
            continue
        sizes = np.bincount(lab.ravel())
        small = sizes < min_px
        small[0] = False
        out[small[lab]] = fill
    return out


def class_areas_km2(cls, pixel_area_m2):
    return {name: float((cls == k).sum() * pixel_area_m2 / 1e6) for k, name in CLASS_NAMES.items()}


# ------------------------------------------------------------------- Ladário
def load_ladario_daily(csv_path, verbose=True):
    """Parse ANA telemetry CSV (15-min) -> daily mean stage. Robust to ; or , and decimal comma."""
    import pandas as pd

    raw = Path(csv_path).read_bytes()[:20000]
    enc = "utf-8"
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        enc = "latin-1"
    txt = raw.decode(enc, errors="ignore")
    sep = ";" if txt.count(";") > txt.count(",") else ","
    df = pd.read_csv(csv_path, sep=sep, encoding=enc, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    import re
    import unicodedata

    def _norm(c):
        c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode().lower()
        return re.sub(r"[^a-z0-9]", "", c)

    low = {c: _norm(c) for c in df.columns}
    if verbose:
        print(f"      CSV sep='{sep}' enc={enc} columns={list(df.columns)}")
        print(df.head(3).to_string(index=False))

    def pick(keys, exclude=()):
        for c, l in low.items():
            if any(k in l for k in keys) and not any(e in l for e in exclude):
                return c
        return None

    tcol = pick(["datahora", "dataehora", "datetime", "timestamp", "dateandtime"])
    def _parse_time(series):
        sample = series.dropna().astype(str).head(20)
        if sample.str.match(r"^\d{4}-\d{2}-\d{2}").all():   # ISO: never day-first
            return pd.to_datetime(series, format="ISO8601", errors="coerce")
        return pd.to_datetime(series, dayfirst=True, errors="coerce")

    if tcol:
        t = _parse_time(df[tcol])
    else:
        dcol, hcol = pick(["data", "date", "dia"], exclude=["hora"]), pick(["hora", "time"])
        if dcol is None:
            raise KeyError("No date/time column recognised; pass column names manually.")
        s = df[dcol] + (" " + df[hcol] if hcol else "")
        t = _parse_time(s)
    lcol = pick(["nivel", "cota", "stage", "level", "altura"], exclude=["status", "flag", "qual"])
    if lcol is None:
        raise KeyError("No stage/level column recognised.")
    lvl = pd.to_numeric(df[lcol].str.replace(",", ".", regex=False), errors="coerce")

    s = pd.Series(lvl.values, index=t).dropna()
    s = s[s.index.notna()].sort_index()
    s = s[~s.index.duplicated()]
    # despike: residual vs 4-h rolling median, drop > 5 robust sigmas
    rm = s.rolling("4h", center=True, min_periods=4).median()
    res = s - rm
    sig = 1.4826 * np.nanmedian(np.abs(res - np.nanmedian(res)))
    lo, hi = np.nanpercentile(s, [1, 99])
    thr = max(5 * sig, 0.05 * (hi - lo))          # floor: MAD can be 0 on quantised, smooth series
    keep = (res.abs() <= thr) | res.isna()
    keep &= s.abs() < 9000                          # sentinel values (9999, -9999)
    n_spikes = int((~keep).sum())
    s = s[keep]
    daily = s.resample("D").agg(["mean", "count"])
    daily.columns = ["stage", "n_obs"]
    meta = dict(time_col=tcol or "date+hour", level_col=lcol, n_raw=int(lvl.notna().sum()),
                n_spikes=n_spikes, start=str(s.index.min()), end=str(s.index.max()))
    return daily, meta
