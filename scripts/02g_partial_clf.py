#!/usr/bin/env python
"""Step 2g (time-boxed to 14:45): can NISAR alone map DSWx "partial surface water"?

Labels : DSWx-HLS 23 Aug (0 not water, 1 open water, 2 partial surface water), mosaicked to the 40 m grid.
Features: NISAR 22 Aug HH, HV, HH-HV (dB), corrected per date by the stable-reference (hills) offset.
Model  : HistGradientBoosting, class-balanced weights.
Baseline: current threshold rule (predicts open water only -> partial F1 = 0 by construction).
Validation:
  A) spatial block CV on 22 Aug (5 km blocks, GroupKFold k=5)
  B) spatio-temporal: each fold's model predicts the OTHER dates, scored only on that fold's held-out blocks
     against the paired DSWx (pairs with >= 80% clear plain).
PRE-REGISTERED SUCCESS (fixed before running):
  (i)  mean partial-water F1 over other dates (B) >= 0.50
  (ii) NISAR partial-water area series (final model, 8 dates) vs Ladário stage: Pearson r >= 0.70 and p < 0.05
Run from the repo root:  python scripts/02g_partial_clf.py
"""
from __future__ import annotations

import glob
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pantanal_sar.classify import WATER, classify, load_ladario_daily  # noqa: E402

TRAIN_N, TRAIN_D = "20260822", "20260823"
BLOCK_PX = 125          # 5 km at 40 m
K = 5
MIN_CLEAR = 80.0
N_SAMPLE = 300_000
F1_MIN, R_MIN, P_MAX = 0.50, 0.70, 0.05
SEED = 42
NAMES = ["not water", "open", "partial"]


def load_dswx_module():
    spec = importlib.util.spec_from_file_location("dswx", ROOT / "scripts/02e_dswx_compare.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_thresholds(path):
    th = {}
    for line in Path(path).read_text().splitlines():
        line = line.split("#")[0].strip()
        if ":" in line:
            k, v = line.split(":", 1)
            th[k.strip()] = float(v)
    return th


def f1_from_cm(cm):
    tp = np.diag(cm).astype(float)
    p = tp / np.maximum(cm.sum(0), 1)
    r = tp / np.maximum(cm.sum(1), 1)
    return 2 * p * r / np.maximum(p + r, 1e-12)


def cm3(y, yhat):
    return np.bincount(3 * y + yhat, minlength=9).reshape(3, 3)


def main():
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.model_selection import GroupKFold
    except ImportError:
        sys.exit("[ERROR] scikit-learn missing: pip install scikit-learn")

    proc, tabs, figs = (ROOT / p for p in ("data/processed", "outputs/tables", "outputs/figures"))
    dswx = load_dswx_module()
    th = read_thresholds(ROOT / "config/thresholds.yaml")
    stab = pd.read_csv(tabs / "stability.csv", dtype={"date": str}).set_index("date")
    pairs_df = pd.read_csv(tabs / "dswx_agreement_all_pairs.csv", dtype={"nisar_date": str, "dswx_date": str})
    pairs = {r.nisar_date: r.dswx_date for r in pairs_df.itertuples() if r.clear_pct >= MIN_CLEAR}
    assert TRAIN_N in pairs, "training pair missing"

    with rasterio.open(proc / "masks_40m.tif") as m:
        urban, high, dem = m.read(1), m.read(2), m.read(3)
        grid = dict(transform=m.transform, crs=m.crs, shape=m.shape)
        pix_area = abs(m.transform.a * m.transform.e)
    plain = (urban == 0) & (high == 0) & np.isfinite(dem)
    H, W = grid["shape"]
    rr, cc = np.indices((H, W))
    block = (rr // BLOCK_PX) * (W // BLOCK_PX + 1) + (cc // BLOCK_PX)

    files = sorted(glob.glob(str(proc / "gcov_*_40m_db.tif")))
    dates = [Path(f).name.split("_")[1] for f in files]
    feats, rule = {}, {}
    for d, f in zip(dates, files):
        with rasterio.open(f) as r:
            hh, hv = r.read(1), r.read(2)
        dhh, dhv = stab.loc[d, "d_hh_stable"], stab.loc[d, "d_hv_stable"]
        hhc, hvc = hh - dhh, hv - dhv
        feats[d] = np.dstack([hhc, hvc, hhc - hvc]).astype("float32")
        rule[d] = (classify(hhc, hvc, th, plain) == WATER).astype("uint8")   # same as shifting thresholds
    common = plain & np.logical_and.reduce([np.isfinite(feats[d]).all(-1) for d in dates])

    labels = {}
    for nd, dd in pairs.items():
        fs = sorted(glob.glob(str(ROOT / f"data/raw/opera_dswx/*_{dd}T*_B01_WTR.tif")))
        w = dswx.mosaic(fs, grid)
        lab = np.full(w.shape, -1, dtype="int8")
        for k in (0, 1, 2):
            lab[w == k] = k
        labels[nd] = lab
    print(f"[1/4] pairs used (>= {MIN_CLEAR:.0f}% clear): " + ", ".join(f"{n[4:]}<-{d[4:]}" for n, d in pairs.items()))

    # ---------------------------------------------------------- training set (22 Aug)
    ok = common & (labels[TRAIN_N] >= 0)
    X_all, y_all, g_all = feats[TRAIN_N][ok], labels[TRAIN_N][ok].astype(int), block[ok]
    frac = np.bincount(y_all, minlength=3) / len(y_all)
    print(f"      train pixels {len(y_all):,} | class share: " +
          " ".join(f"{NAMES[k]} {100 * frac[k]:.1f}%" for k in range(3)) + f" | blocks {len(np.unique(g_all))}")
    rng = np.random.default_rng(SEED)

    def fit(idx):
        if len(idx) > N_SAMPLE:
            idx = rng.choice(idx, N_SAMPLE, replace=False)
        y = y_all[idx]
        cw = len(y) / (3 * np.maximum(np.bincount(y, minlength=3), 1))
        mdl = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, max_leaf_nodes=31,
                                             l2_regularization=1.0, random_state=SEED)
        mdl.fit(X_all[idx], y, sample_weight=cw[y])
        return mdl

    # ---------------------------------------------------------- A + B
    others = [d for d in pairs if d != TRAIN_N]
    cmA_m, cmA_b = np.zeros((3, 3), int), np.zeros((3, 3), int)
    cmB_m = {d: np.zeros((3, 3), int) for d in others}
    cmB_b = {d: np.zeros((3, 3), int) for d in others}
    gkf = GroupKFold(n_splits=K)
    for k, (tr, te) in enumerate(gkf.split(X_all, y_all, g_all)):
        mdl = fit(tr)
        cmA_m += cm3(y_all[te], mdl.predict(X_all[te]))
        rule_tr = rule[TRAIN_N][ok]
        cmA_b += cm3(y_all[te], rule_tr[te].astype(int))
        test_blocks = np.isin(block, np.unique(g_all[te]))
        for d in others:
            mk = common & test_blocks & (labels[d] >= 0)
            y = labels[d][mk].astype(int)
            cmB_m[d] += cm3(y, mdl.predict(feats[d][mk]))
            cmB_b[d] += cm3(y, rule[d][mk].astype(int))
        print(f"      fold {k + 1}/{K} done")

    fA_m, fA_b = f1_from_cm(cmA_m), f1_from_cm(cmA_b)
    print("[2/4] A) spatial block CV on 22 Aug — F1 per class (not water / open / partial):")
    print(f"      model   : {fA_m[0]:.2f} / {fA_m[1]:.2f} / {fA_m[2]:.2f}")
    print(f"      baseline: {fA_b[0]:.2f} / {fA_b[1]:.2f} / {fA_b[2]:.2f}   (rule has no partial class)")
    rows = []
    print("      B) other dates, held-out blocks only — F1 open / partial (model) | F1 open (baseline):")
    for d in others:
        fm, fb = f1_from_cm(cmB_m[d]), f1_from_cm(cmB_b[d])
        rows.append(dict(date=d, dswx=pairs[d], f1_open_model=fm[1], f1_partial_model=fm[2],
                         f1_notwater_model=fm[0], f1_open_baseline=fb[1], n=int(cmB_m[d].sum())))
        print(f"      {d}  {fm[1]:.2f} / {fm[2]:.2f} | {fb[1]:.2f}")
    met = pd.DataFrame(rows)
    f1p = met["f1_partial_model"].mean()
    met.to_csv(tabs / "partial_clf_metrics.csv", index=False, float_format="%.3f")

    # ---------------------------------------------------------- final model + series
    mdl = fit(np.arange(len(y_all)))
    daily, _ = load_ladario_daily(ROOT / "data/external/ladario_gauge/ladario_stage_raw_telemetria.csv",
                                  verbose=False)
    preds, ser = {}, []
    for d in dates:
        p = np.full((H, W), 255, dtype="uint8")
        p[common] = mdl.predict(feats[d][common]).astype("uint8")
        preds[d] = p
        ser.append(dict(date=d, nisar_open_km2=(p == 1).sum() * pix_area / 1e6,
                        nisar_partial_km2=(p == 2).sum() * pix_area / 1e6,
                        stage_cm=daily["stage"].get(pd.Timestamp(f"{d[:4]}-{d[4:6]}-{d[6:]}"), np.nan)))
    s = pd.DataFrame(ser)
    s["nisar_open_partial_km2"] = s["nisar_open_km2"] + s["nisar_partial_km2"]
    s.to_csv(tabs / "partial_clf_series.csv", index=False, float_format="%.2f")
    r_p, p_p = stats.pearsonr(s["stage_cm"], s["nisar_partial_km2"])
    r_op, p_op = stats.pearsonr(s["stage_cm"], s["nisar_open_partial_km2"])
    print("[3/4] final model (all 22 Aug labels) applied to 8 dates (plain, common valid):")
    print(s.round(1).to_string(index=False))
    print(f"      partial vs Ladário: r={r_p:.2f} (p={p_p:.3f}) | open+partial vs Ladário: r={r_op:.2f} (p={p_op:.3f})")

    ok_i, ok_ii = f1p >= F1_MIN, (r_p >= R_MIN) and (p_p < P_MAX)
    success = ok_i and ok_ii
    print(f"[4/4] PRE-REGISTERED: (i) mean partial F1 other dates = {f1p:.2f} (>= {F1_MIN}) -> {'PASS' if ok_i else 'FAIL'}"
          f" | (ii) partial series r = {r_p:.2f}, p = {p_p:.3f} (r >= {R_MIN}, p < {P_MAX}) -> {'PASS' if ok_ii else 'FAIL'}")
    print(f"      => {'SUCCESS' if success else 'NEGATIVE RESULT'}")
    if success:
        summary = (f"Yes. A gradient-boosting classifier on HH, HV and HH−HV, trained on DSWx-HLS labels of 23 Aug, "
                   f"maps partial surface water on other dates with mean F1 = {f1p:.2f} (spatial-block hold-out), "
                   f"and its partial-water series tracks Ladário (r = {r_p:.2f}, p = {p_p:.3f}). "
                   f"The threshold baseline cannot map this class (F1 = 0).")
    else:
        summary = (f"Not with backscatter alone (pre-registered test failed): a classifier on HH, HV and HH−HV trained on "
                   f"DSWx-HLS labels of 23 Aug reached a mean partial-water F1 of {f1p:.2f} on other dates "
                   f"(target ≥ {F1_MIN}) and its partial-water series gave r = {r_p:.2f} with Ladário (target ≥ {R_MIN}). "
                   f"Next steps: texture, coherence (GUNW) and multi-date features.")
    print(f"      README text: {summary}")
    pd.DataFrame([dict(summary=summary, f1_partial_mean=f1p, r_partial=r_p, p_partial=p_p,
                       success=success)]).to_csv(tabs / "partial_clf_summary.csv", index=False)

    # ---------------------------------------------------------- figures
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap

    comp = pd.read_csv(tabs / "dswx_comparison.csv", dtype={"nisar_date": str, "dswx_date": str})
    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    t = pd.to_datetime(s["date"])
    ax.plot(t, s["nisar_partial_km2"], "o-", color="#2ca25f", label="NISAR partial water (classifier)")
    ax.plot(t, s["nisar_open_km2"], "o-", color="#1f4e9c", label="NISAR open water (classifier)")
    ax.plot(pd.to_datetime(comp["dswx_date"]), comp["series_dswx_open_partial_km2"] - comp["series_dswx_open_km2"],
            "s--", color="#fdae6b", label="DSWx partial water (common clear pixels)")
    ax.set_ylabel("area (km²)")
    a2 = ax.twinx()
    st = daily.loc[t.min() - pd.Timedelta(days=10): t.max() + pd.Timedelta(days=10), "stage"]
    a2.plot(st.index, st.values, color="0.5", lw=1)
    a2.set_ylabel("Ladário stage (cm)", color="0.4")
    ax.legend(fontsize=8, loc="upper right")
    ax.set_title(f"NISAR partial-water classifier — {'success' if success else 'negative result'} "
                 f"(F1 partial {f1p:.2f}, r {r_p:.2f})")
    fig.savefig(figs / "partial_clf_series.png", dpi=120)
    plt.close(fig)

    cm = ListedColormap(["#efe6cf", "#1f4e9c", "#2ca25f"])
    fig, ax = plt.subplots(1, 2, figsize=(14, 10), constrained_layout=True)
    for a, img, ttl in [(ax[0], np.ma.masked_equal(preds[TRAIN_N], 255), f"NISAR classifier {TRAIN_N}"),
                        (ax[1], np.ma.masked_less(np.where(common, labels[TRAIN_N], -1), 0), f"DSWx-HLS {TRAIN_D}")]:
        a.imshow(img, cmap=cm, vmin=0, vmax=2, interpolation="nearest")
        a.set_title(ttl + "  (beige not water, blue open, green partial)", fontsize=9)
        a.set_axis_off()
    fig.savefig(figs / f"partial_clf_map_{TRAIN_N}.png", dpi=110)
    plt.close(fig)
    print(f"      figures: {figs}/partial_clf_series.png, partial_clf_map_{TRAIN_N}.png")


if __name__ == "__main__":
    main()
