"""NISAR L2 GCOV preprocessing: read -> clip to AOI -> multilook -> Lee filter -> dB.

All filtering is done in linear power (gamma0); dB conversion is the last step.
"""
from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import h5py
import numpy as np
from pyproj import Transformer
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from scipy.ndimage import uniform_filter
from shapely import wkt
from shapely.geometry import mapping, shape
from shapely.ops import transform as shp_transform

# Fallback AOI (same as config/aoi.geojson, EPSG:4326)
AOI_WKT_FALLBACK = (
    "POLYGON((-57.95 -19.08, -57.30 -19.08, -57.30 -17.95, "
    "-57.95 -17.95, -57.95 -19.08))"
)


# --------------------------------------------------------------------------- AOI
def load_aoi(path: str | Path | None):
    """Return AOI polygon in lon/lat (EPSG:4326)."""
    if path and Path(path).exists():
        gj = json.loads(Path(path).read_text())
        if gj.get("type") == "FeatureCollection":
            geom = gj["features"][0]["geometry"]
        elif gj.get("type") == "Feature":
            geom = gj["geometry"]
        else:
            geom = gj
        return shape(geom)
    warnings.warn(f"AOI file not found ({path}); using hard-coded AOI WKT.")
    return wkt.loads(AOI_WKT_FALLBACK)


# ------------------------------------------------------------------ HDF5 helpers
def find_freq_group(h5: h5py.File, freq: str = "frequencyA") -> str:
    """Locate .../grids/frequencyA (the group holding HHHH) without hard-coding the path."""
    found: list[str] = []

    def visit(name, obj):
        if isinstance(obj, h5py.Group) and name.endswith(freq) and "HHHH" in obj:
            found.append(name)

    h5.visititems(visit)
    if not found:
        raise KeyError(f"No group ending in '{freq}' containing HHHH was found.")
    return found[0]


def read_epsg(grp: h5py.Group) -> int:
    if "projection" in grp:
        p = grp["projection"]
        for key in ("epsg_code", "epsg"):
            if key in p.attrs:
                return int(np.asarray(p.attrs[key]).ravel()[0])
        try:
            val = int(np.asarray(p[()]).ravel()[0])
            if val > 1000:
                return val
        except Exception:
            pass
    raise KeyError("Could not read EPSG code from the 'projection' dataset.")


# --------------------------------------------------------------------- results
@dataclass
class Clip:
    bands: dict[str, np.ndarray]          # linear gamma0, float32, NaN = nodata
    transform: object                     # affine, north-up
    epsg: int
    spacing: float                        # native pixel size (m)
    nlooks: np.ndarray | None = None
    meta: dict = field(default_factory=dict)


# -------------------------------------------------------------------- reading
def read_clip(path: str | Path, aoi_ll, pols=("HHHH", "HVHV"), freq="frequencyA") -> Clip:
    """Read only the AOI window from the GCOV HDF5 (no full-frame load)."""
    with h5py.File(path, "r") as f:
        gpath = find_freq_group(f, freq)
        g = f[gpath]
        epsg = read_epsg(g)
        x = g["xCoordinates"][()].astype("float64")
        y = g["yCoordinates"][()].astype("float64")
        dx = float(np.median(np.diff(x)))
        dy = float(np.median(np.diff(y)))

        tr = Transformer.from_crs(4326, epsg, always_xy=True)
        aoi_dense = aoi_ll.segmentize(0.01) if hasattr(aoi_ll, "segmentize") else aoi_ll
        aoi_xy = shp_transform(tr.transform, aoi_dense)
        xmin, ymin, xmax, ymax = aoi_xy.bounds

        ix = np.where((x >= xmin) & (x <= xmax))[0]
        iy = np.where((y >= ymin) & (y <= ymax))[0]
        if ix.size == 0 or iy.size == 0:
            raise ValueError("AOI does not overlap this GCOV frame.")
        c0, c1 = ix.min(), ix.max() + 1
        r0, r1 = iy.min(), iy.max() + 1

        bands = {}
        for p in pols:
            if p not in g:
                raise KeyError(f"Polarization {p} not in {gpath}. Available: {list(g.keys())}")
            a = g[p][r0:r1, c0:c1].astype("float32")
            a[~np.isfinite(a) | (a <= 0)] = np.nan
            bands[p] = a
        nlooks = g["numberOfLooks"][r0:r1, c0:c1].astype("float32") if "numberOfLooks" in g else None

    # Make north-up (rows go north -> south)
    if dy > 0:
        bands = {k: v[::-1] for k, v in bands.items()}
        nlooks = nlooks[::-1] if nlooks is not None else None
    if dx < 0:
        bands = {k: v[:, ::-1] for k, v in bands.items()}
        nlooks = nlooks[:, ::-1] if nlooks is not None else None

    xs, ys = x[c0:c1], y[r0:r1]
    px, py = abs(dx), abs(dy)
    # Coordinates are pixel centres -> shift by half a pixel to get the corner
    transform = from_origin(xs.min() - px / 2, ys.max() + py / 2, px, py)
    return Clip(bands, transform, epsg, px, nlooks,
                meta={"h5_group": gpath, "aoi_xy": aoi_xy, "dy_native": dy})


# ----------------------------------------------------------------- processing
def multilook(a: np.ndarray, f: int) -> np.ndarray:
    """f x f block mean in linear power, NaN-aware."""
    if f <= 1:
        return a
    h, w = (a.shape[0] // f) * f, (a.shape[1] // f) * f
    b = a[:h, :w].reshape(h // f, f, w // f, f)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmean(b, axis=(1, 3)).astype("float32")


def _local_moments(img: np.ndarray, size: int):
    valid = np.isfinite(img)
    z = np.where(valid, img, 0.0).astype("float64")
    w = uniform_filter(valid.astype("float64"), size, mode="reflect")
    with np.errstate(invalid="ignore", divide="ignore"):
        m = uniform_filter(z, size, mode="reflect") / w
        m2 = uniform_filter(z * z, size, mode="reflect") / w
    var = np.maximum(m2 - m * m, 0.0)
    return m, var, valid, w


def estimate_enl(img: np.ndarray, size: int = 7) -> float:
    """Data-driven ENL: median of local mean^2/var over full windows.

    Heterogeneous windows push it down, so it is a conservative (stronger-filtering) estimate.
    """
    m, var, valid, w = _local_moments(img, size)
    ok = valid & (w > 0.999) & (var > 0)
    if ok.sum() < 100:
        return 4.0
    return float(np.median(m[ok] ** 2 / var[ok]))


def lee_filter(img: np.ndarray, size: int = 5, enl: float = 4.0) -> np.ndarray:
    """Lee filter (Lopes form) for intensity data, NaN-aware."""
    m, var, valid, _ = _local_moments(img, size)
    cu2 = 1.0 / enl
    with np.errstate(invalid="ignore", divide="ignore"):
        ci2 = var / (m * m)
        k = (1.0 - cu2 / ci2) / (1.0 + cu2)
    k = np.clip(np.nan_to_num(k, nan=0.0), 0.0, 1.0)
    z = np.where(valid, img, m)
    out = m + k * (z - m)
    out[~valid] = np.nan
    return out.astype("float32")


def to_db(a: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        return (10.0 * np.log10(np.clip(a, 1e-6, None))).astype("float32")


def aoi_mask(aoi_xy, shape_, transform) -> np.ndarray:
    """True inside the AOI polygon."""
    return geometry_mask([mapping(aoi_xy)], out_shape=shape_, transform=transform, invert=True)
