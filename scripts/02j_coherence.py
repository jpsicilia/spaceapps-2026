#!/usr/bin/env python
# AI-assisted: written with Claude (Anthropic) from the author’s specifications; reviewed and run by the author. See docs/ai_use.md
"""Step 2j (extension, exploratory; time-boxed to 19:00): does InSAR coherence help separate DSWx partial water
from not-water, where backscatter alone failed?

Data   : NISAR L2 GUNW 2026-08-10 -> 2026-08-22 (best pair in our QA), layer coherenceMagnitude, averaged onto the
         40 m grid. Labels: DSWx-HLS 2026-08-23 (0 not water, 1 open, 2 partial), floodplain mask as in 02c.
(1) Descriptive: median and IQR of coherence per DSWx class inside the floodplain.
(2) Test: same classifier, same 5 km spatial blocks (GroupKFold k=5), same seed and sampling as 02g (validation A on
    22 Aug), WITHOUT and WITH coherence as a 4th feature, on exactly the same pixels (coherence valid).
PRE-REGISTERED CRITERION (fixed before running): success if the partial-water F1 WITH coherence is >= 0.50
    (reference: 0.35 without coherence in 02g); otherwise negative result.
Spatial CV on one date only: there is no coherence for other dates, so no temporal transfer is tested.
Writes outputs/tables/coherence_test.csv and outputs/figures/coherence_test.png.
Run from the repo root:  python scripts/02j_coherence.py
"""
from __future__ import annotations

import glob
import importlib.util
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

D0, D1, NISAR_D, DSWX_D = "20260810", "20260822", "20260822", "20260823"
BLOCK_PX, K, N_SAMPLE, SEED = 125, 5, 300_000, 42          # identical to 02g_partial_clf.py
F1_TARGET, F1_REF = 0.50, 0.35
NAMES = ["not water", "open", "partial"]


def find_gunw():
    fs = [f for f in glob.glob(str(ROOT / "data/raw/nisar_gunw/**/*.h5"), recursive=True)
          if D0 in Path(f).name and D1 in Path(f).name]
    if not fs:
        sys.exit(f"[ERROR] no GUNW .h5 with {D0} and {D1} in its name under data/raw/nisar_gunw/")
    return sorted(fs)[0]


def read_coherence(path, grid):
    """Find every coherenceMagnitude layer, take the finest one, read only the AOI window, average to the grid."""
    from pyproj import Transformer
    from rasterio.transform import array_bounds
    with h5py.File(path, "r") as f:
        cands = []
        f.visititems(lambda n, o: cands.append(n) if isinstance(o, h5py.Dataset) and n.endswith("coherenceMagnitude") else None)
        if not cands:
            sys.exit(f"[ERROR] no coherenceMagnitude dataset in {Path(path).name}")
        info = []
        for c in cands:
            g = f[c].parent
            gg, x, y, epsg = g, None, None, None
            while gg.name != "/" and (x is None or epsg is None):
                if x is None and "xCoordinates" in gg and len(gg["xCoordinates"]) == f[c].shape[1]:
                    x, y = gg["xCoordinates"][()], gg["yCoordinates"][()]
                if epsg is None and "projection" in gg:
                    p = gg["projection"]
                    epsg = int(np.asarray(p.attrs.get("epsg_code", p[()])).ravel()[0])
                gg = gg.parent
            if x is not None and epsg:
                info.append((abs(float(np.median(np.diff(x)))), c, x, y, epsg))
        if not info:
            sys.exit(f"[ERROR] could not locate coordinates/projection for {cands}")
        dx, name, x, y, epsg = sorted(info, key=lambda t: t[0])[0]
        print(f"[1/4] {Path(path).name}\n      layer {name}  spacing {dx:.0f} m  EPSG:{epsg}  "
              f"(candidates: {', '.join(c for c in cands)})")
        H, W = grid["shape"]
        l, b, r, t = array_bounds(H, W, grid["transform"])
        if str(grid["crs"].to_epsg()) != str(epsg):
            tr = Transformer.from_crs(grid["crs"], epsg, always_xy=True)
            xs, ys = tr.transform([l, r, l, r], [b, b, t, t])
            l, r, b, t = min(xs), max(xs), min(ys), max(ys)
        pad = 4 * dx
        ix = np.where((x >= l - pad) & (x <= r + pad))[0]
        iy = np.where((y >= b - pad) & (y <= t + pad))[0]
        c0, c1, r0, r1 = ix.min(), ix.max() + 1, iy.min(), iy.max() + 1
        a = f[name][r0:r1, c0:c1].astype("float32")
    a[~np.isfinite(a) | (a < 0) | (a > 1)] = np.nan
    xs, ys = x[c0:c1], y[r0:r1]
    dy = float(np.median(np.diff(y)))
    if dy > 0:
        a, ys = a[::-1], ys[::-1]
    src_tr = from_origin(xs.min() - dx / 2, ys.max() + abs(dy) / 2, dx, abs(dy))
    out = np.full(grid["shape"], np.nan, dtype="float32")
    reproject(a, out, src_transform=src_tr, src_crs=f"EPSG:{epsg}", dst_transform=grid["transform"],
              dst_crs=grid["crs"], src_nodata=np.nan, dst_nodata=np.nan, resampling=Resampling.average)
    return out


def f1_from_cm(cm):
    tp = np.diag(cm).astype(float)
    p, r = tp / np.maximum(cm.sum(0), 1), tp / np.maximum(cm.sum(1), 1)
    return 2 * p * r / np.maximum(p + r, 1e-12)


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.model_selection import GroupKFold

    proc, tabs, figs = (ROOT / p for p in ("data/processed", "outputs/tables", "outputs/figures"))
    with rasterio.open(proc / "masks_40m.tif") as m:
        urban, high, dem = m.read(1), m.read(2), m.read(3)
        grid = dict(transform=m.transform, crs=m.crs, shape=m.shape)
    plain = (urban == 0) & (high == 0) & np.isfinite(dem)
    coh = read_coherence(find_gunw(), grid)

    stab = pd.read_csv(tabs / "stability.csv", dtype={"date": str}).set_index("date")
    with rasterio.open(proc / f"gcov_{NISAR_D}_40m_db.tif") as r:
        hh = r.read(1) - stab.loc[NISAR_D, "d_hh_stable"]
        hv = r.read(2) - stab.loc[NISAR_D, "d_hv_stable"]
    spec = importlib.util.spec_from_file_location("dswx", ROOT / "scripts/02e_dswx_compare.py")
    dswx = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dswx)
    w = dswx.mosaic(sorted(glob.glob(str(ROOT / f"data/raw/opera_dswx/*_{DSWX_D}T*_B01_WTR.tif"))), grid)

    ok = plain & np.isfinite(hh) & np.isfinite(hv) & np.isfinite(coh) & np.isin(w, (0, 1, 2))
    y_all = w[ok].astype(int)
    n_plain = (plain & np.isin(w, (0, 1, 2)) & np.isfinite(hh)).sum()
    print(f"      pixels with coherence, labels and backscatter: {ok.sum():,} ({100 * ok.sum() / n_plain:.1f}% of "
          f"labelled floodplain)")

    # (1) descriptive
    rows = []
    print("[2/4] coherence by DSWx class (floodplain, 23 Aug labels, 10→22 Aug pair):")
    for k, nm in enumerate(NAMES):
        v = coh[ok][y_all == k]
        q25, q50, q75 = np.percentile(v, [25, 50, 75])
        rows.append(dict(kind="descriptive", label=nm, n=len(v), median=q50, q25=q25, q75=q75))
        print(f"      {nm:10} n={len(v):>9,}  median {q50:.3f}  IQR {q25:.3f}–{q75:.3f}")

    # (2) test: identical setup to 02g validation A, on the same pixels, without/with coherence
    H, W = grid["shape"]
    rr, cc = np.indices((H, W))
    block = ((rr // BLOCK_PX) * (W // BLOCK_PX + 1) + (cc // BLOCK_PX))[ok]
    X3 = np.column_stack([hh[ok], hv[ok], hh[ok] - hv[ok]]).astype("float32")
    X4 = np.column_stack([X3, coh[ok]]).astype("float32")
    res = {}
    for label, X in (("backscatter (HH, HV, HH−HV)", X3), ("backscatter + coherence", X4)):
        rng = np.random.default_rng(SEED)
        cm = np.zeros((3, 3), int)
        for tr_i, te_i in GroupKFold(n_splits=K).split(X, y_all, block):
            idx = rng.choice(tr_i, N_SAMPLE, replace=False) if len(tr_i) > N_SAMPLE else tr_i
            yt = y_all[idx]
            cw = len(yt) / (3 * np.maximum(np.bincount(yt, minlength=3), 1))
            mdl = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, max_leaf_nodes=31,
                                                 l2_regularization=1.0, random_state=SEED)
            mdl.fit(X[idx], yt, sample_weight=cw[yt])
            cm += np.bincount(3 * y_all[te_i] + mdl.predict(X[te_i]), minlength=9).reshape(3, 3)
        f1 = f1_from_cm(cm)
        res[label] = f1
        rows.append(dict(kind="test", label=label, n=int(cm.sum()), f1_not_water=f1[0], f1_open=f1[1], f1_partial=f1[2]))
    print("[3/4] spatial-block CV on 22 Aug, same pixels — F1 (not water / open / partial):")
    for label, f1 in res.items():
        print(f"      {label:30} {f1[0]:.2f} / {f1[1]:.2f} / {f1[2]:.2f}")

    f_without, f_with = res["backscatter (HH, HV, HH−HV)"][2], res["backscatter + coherence"][2]
    success = f_with >= F1_TARGET
    print(f"[4/4] PRE-REGISTERED: partial F1 with coherence = {f_with:.2f} (target ≥ {F1_TARGET}; without = "
          f"{f_without:.2f}, 02g reference {F1_REF}) => {'SUCCESS' if success else 'NEGATIVE RESULT'}")
    rows.append(dict(kind="verdict", label="success" if success else "negative", f1_partial=f_with,
                     f1_partial_without=f_without, target=F1_TARGET, pair=f"{D0}-{D1}", labels=DSWX_D))
    pd.DataFrame(rows).to_csv(tabs / "coherence_test.csv", index=False, float_format="%.4f")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rng = np.random.default_rng(SEED)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    data = []
    for k in range(3):
        v = coh[ok][y_all == k]
        data.append(rng.choice(v, min(len(v), 50_000), replace=False))
    try:
        ax[0].boxplot(data, tick_labels=NAMES, showfliers=False)
    except TypeError:                      # matplotlib < 3.9
        ax[0].boxplot(data, labels=NAMES, showfliers=False)
    ax[0].set_ylabel("InSAR coherence (10→22 Aug)")
    ax[0].set_title("Coherence by DSWx class (23 Aug), floodplain")
    labs = ["without coherence", "with coherence"]
    ax[1].bar(labs, [f_without, f_with], color=["#9aa3ad", "#0f766e"])
    ax[1].axhline(F1_TARGET, color="k", ls="--", lw=1, label=f"pre-registered target {F1_TARGET}")
    ax[1].set_ylim(0, 1)
    ax[1].set_ylabel("partial-water F1 (spatial-block CV, 22 Aug)")
    ax[1].set_title("Success" if success else "Negative result")
    ax[1].legend(frameon=False)
    fig.savefig(figs / "coherence_test.png", dpi=150)
    print(f"      {tabs / 'coherence_test.csv'}, {figs / 'coherence_test.png'}")


if __name__ == "__main__":
    main()
