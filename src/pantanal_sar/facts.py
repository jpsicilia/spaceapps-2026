# AI-assisted: written with Claude (Anthropic) from the author’s specifications; reviewed and run by the author. See docs/ai_use.md
"""Single source of every number shown in README, web, slides, script and submission.

Each fact = value (raw), shown (as displayed), source (file + column/row or script).
Everything is read from versioned tables in outputs/tables/ and config/, so anyone can audit it
from the repository alone (no raw data needed).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from scipy import stats

T = "outputs/tables"
EXPECTED_TILES = ["T21KUA", "T21KUU", "T21KUV", "T21KVA", "T21KVU", "T21KVV"]   # docs/data_inventory.md (6 MGRS tiles)
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def dm(s: str) -> str:
    s = str(s).replace("-", "")
    return f"{int(s[6:8])} {MON[int(s[4:6]) - 1]}"


def repeat_text(dates) -> str:
    """'on a 12-day repeat (one 24-day gap, 17 Jul–10 Aug: cycle 026 not available)' from the actual dates."""
    ds = [date.fromisoformat(str(d)[:10]) for d in dates]
    gaps = [(a, b, (b - a).days) for a, b in zip(ds, ds[1:])]
    base = min(g[2] for g in gaps)
    long = [g for g in gaps if g[2] > base]
    txt = f"on a {base}-day repeat"
    if len(long) == 1:
        a, b, n = long[0]
        txt += (f" (one {n}-day gap, {a.day} {MON[a.month - 1]}–{b.day} {MON[b.month - 1]}: "
                "cycle 026 not available)")
    elif long:
        txt += f" ({len(long)} longer gaps)"
    return txt


def load_facts(root: Path) -> dict:
    r = Path(root)
    t = lambda n: pd.read_csv(r / T / n, dtype={"date": str, "nisar_date": str, "dswx_date": str})  # noqa: E731
    area, agr, comp = t("area_series.csv"), t("dswx_agreement_all_pairs.csv"), t("dswx_comparison.csv")
    loss = t("jul_aug_loss.csv").iloc[0]
    trans = pd.read_csv(r / T / "jul_aug_loss_dswx_transitions.csv", index_col=0)
    wind = t("wind_check.csv").iloc[0]
    clf = t("partial_clf_summary.csv").iloc[0]
    clfm = t("partial_clf_metrics.csv")
    chg = t("change_20260717_20261021.csv").set_index("code")
    cov = t("sep_optical_coverage.csv").iloc[0]
    th = {}
    for line in (r / "config/thresholds.yaml").read_text().splitlines():
        line = line.split("#")[0].strip()
        if ":" in line:
            k, v = line.split(":", 1)
            th[k.strip()] = float(v)

    F = {}

    def add(fid, label, value, shown, source):
        F[fid] = dict(id=fid, label=label, value=value, shown=shown, source=source)

    s0, s1 = area["stage_cm"].iloc[0], area["stage_cm"].iloc[-1]
    add("F01", "Ladário stage on first NISAR date", s0, f"{s0:.0f} cm", f"{T}/area_series.csv: stage_cm, row date={area['date'].iloc[0]}")
    add("F02", "Ladário stage on last NISAR date", s1, f"{s1:.0f} cm", f"{T}/area_series.csv: stage_cm, row date={area['date'].iloc[-1]}")
    add("F03", "River fall between first and last NISAR date", (s0 - s1) / 100, f"~{(s0 - s1) / 100:.1f} m",
        "F01 − F02")
    add("F04", "Number of NISAR GCOV dates", len(area), f"{len(area)}", f"{T}/area_series.csv: row count")
    add("F05", "NISAR revisit", None, repeat_text(area["date"]),
        f"{T}/area_series.csv: date (differences); cycle 026 status from docs/data_inventory.md")
    add("F06", "Open-water thresholds", (th["water_hv_max"], th["water_hh_max"]),
        f"HV < {th['water_hv_max']:.0f} dB and HH < {th['water_hh_max']:.0f} dB",
        "config/thresholds.yaml: water_hv_max, water_hh_max")
    add("F07", "Precision of NISAR open water vs DSWx-HLS (range)", (agr.precision.min(), agr.precision.max()),
        f"{agr.precision.min():.2f}–{agr.precision.max():.2f}", f"{T}/dswx_agreement_all_pairs.csv: precision (min–max)")
    add("F08", "Recall (range)", (agr.recall.min(), agr.recall.max()),
        f"{agr.recall.min():.2f}–{agr.recall.max():.2f}", f"{T}/dswx_agreement_all_pairs.csv: recall (min–max)")
    add("F09", "IoU (range)", (agr.iou.min(), agr.iou.max()),
        f"{agr.iou.min():.2f}–{agr.iou.max():.2f}", f"{T}/dswx_agreement_all_pairs.csv: iou (min–max)")
    add("F10", "Number of NISAR–DSWx pairs", len(agr), f"{len(agr)}", f"{T}/dswx_agreement_all_pairs.csv: row count")
    ratio = (comp.series_nisar_km2 / comp.series_dswx_open_km2).mean()
    add("F11", "Share of DSWx open-water area recovered by NISAR (mean)", ratio, f"{100 * ratio:.0f}%",
        f"{T}/dswx_comparison.csv: mean(series_nisar_km2 / series_dswx_open_km2)")
    add("F12", "DSWx open water, first → last common date", (comp.series_dswx_open_km2.iloc[0], comp.series_dswx_open_km2.iloc[-1]),
        f"{comp.series_dswx_open_km2.iloc[0]:.0f} → {comp.series_dswx_open_km2.iloc[-1]:.0f} km²",
        f"{T}/dswx_comparison.csv: series_dswx_open_km2, first and last row")
    r_o, p_o = stats.pearsonr(comp.stage_at_dswx_cm, comp.series_dswx_open_km2)
    add("F13", "DSWx open water vs Ladário (Pearson)", (r_o, p_o), f"r = {r_o:.2f}, p = {p_o:.2f}",
        f"{T}/dswx_comparison.csv: pearsonr(stage_at_dswx_cm, series_dswx_open_km2)")
    add("F14", "DSWx open + partial water, first → last", (comp.series_dswx_open_partial_km2.iloc[0], comp.series_dswx_open_partial_km2.iloc[-1]),
        f"{comp.series_dswx_open_partial_km2.iloc[0]:.0f} → {comp.series_dswx_open_partial_km2.iloc[-1]:.0f} km²",
        f"{T}/dswx_comparison.csv: series_dswx_open_partial_km2, first and last row")
    r_p, p_p = stats.pearsonr(comp.stage_at_dswx_cm, comp.series_dswx_open_partial_km2)
    add("F15", "DSWx open + partial vs Ladário (Pearson)", (r_p, p_p), f"r = {r_p:.2f}, p = {p_p:.3f}",
        f"{T}/dswx_comparison.csv: pearsonr(stage_at_dswx_cm, series_dswx_open_partial_km2)")
    r_n, p_n = stats.pearsonr(comp.stage_at_dswx_cm, comp.series_nisar_km2)
    add("F16", "NISAR open water vs Ladário (Pearson)", (r_n, p_n), f"r = {r_n:.2f}, p = {p_n:.2f}",
        f"{T}/dswx_comparison.csv: pearsonr(stage_at_dswx_cm, series_nisar_km2)")
    add("F17", "Number of dates in the common valid (clear) series", len(comp), f"{len(comp)}",
        f"{T}/dswx_comparison.csv: row count (pairs with ≥ 80% clear)")
    w0, w1 = area["water_km2"].iloc[0], area["water_km2"].iloc[1]
    add("F18", "NISAR open water 17 Jul → 10 Aug", (w0, w1), f"{w0:.0f} → {w1:.0f} km²",
        f"{T}/area_series.csv: water_km2, rows 1–2")
    add("F19", "NISAR open water lost 17 Jul → 10 Aug", loss.lost_km2, f"{loss.lost_km2:.0f} km²",
        f"{T}/jul_aug_loss.csv: lost_km2")
    add("F20", "…of which on DSWx-clear pixels", loss.lost_clear_km2, f"{loss.lost_clear_km2:.0f} km²",
        f"{T}/jul_aug_loss.csv: lost_clear_km2")
    add("F21", "Share of the loss on DSWx partial water (19 Jul)", loss.lost_partial_pct, f"{loss.lost_partial_pct:.0f}%",
        f"{T}/jul_aug_loss.csv: lost_partial_pct (pre-registered rule: > 50%)")
    add("F22", "Partial-water enrichment on lost pixels vs plain", loss.enrichment, f"×{loss.enrichment:.1f}",
        f"{T}/jul_aug_loss.csv: enrichment")
    pp, oo = float(trans.loc["partial", "partial"]), float(trans.loc["open", "open"])
    add("F23", "Lost pixels still partial water in DSWx 8 Aug", pp, f"{pp:.0f} km²",
        f"{T}/jul_aug_loss_dswx_transitions.csv: row partial, column partial")
    add("F24", "Lost pixels still open water in DSWx 8 Aug", oo, f"{oo:.0f} km²",
        f"{T}/jul_aug_loss_dswx_transitions.csv: row open, column open")
    add("F25", "Unexplained share of the drop", oo / loss.lost_clear_km2, f"{100 * oo / loss.lost_clear_km2:.0f}% (about a third)",
        "F24 / F20")
    add("F26", "Wind check: HH change in permanent water, Aug vs 17 Jul (offset-corrected)", (wind.d_hh, wind.d_hv),
        f"HH {wind.d_hh:+.1f} dB, HV {wind.d_hv:+.1f} dB", f"{T}/wind_check.csv: d_hh, d_hv (pre-registered rule: ≥ +1.0 dB)")
    add("F27", "Partial-water classifier: mean F1 on other dates", clf.f1_partial_mean, f"{clf.f1_partial_mean:.2f} (target ≥ 0.50)",
        f"{T}/partial_clf_summary.csv: f1_partial_mean")
    add("F28", "Partial-water classifier: series vs Ladário", clf.r_partial, f"r = {clf.r_partial:.2f} (target ≥ 0.70)",
        f"{T}/partial_clf_summary.csv: r_partial")
    add("F29", "Classifier partial F1 by date (range)", (clfm.f1_partial_model.min(), clfm.f1_partial_model.max()),
        f"{clfm.f1_partial_model.min():.2f}–{clfm.f1_partial_model.max():.2f}", f"{T}/partial_clf_metrics.csv: f1_partial_model")
    add("F30", "Optical (DSWx) coverage of the floodplain on 2 Sep", cov.clear_pct, f"{cov.clear_pct:.1f}%",
        f"{T}/sep_optical_coverage.csv: clear_pct")
    files = pd.read_csv(r / T / "dswx_coverage_files.csv")
    present = sorted(set(files["tile"]))
    missing = [t_ for t_ in EXPECTED_TILES if t_ not in present]
    sensors = sorted(set(files.loc[files["valid_km2"] > 0, "sensor"]))
    if len(missing) != 1 or sensors != ["S2B"]:
        raise ValueError(f"2 Sep tile check changed: missing={missing}, sensors with valid data={sensors}; "
                         "update the F31 wording")
    gap = (f"no HLS/DSWx product exists that day for tile {missing[0][1:]}, "
           f"although Sentinel-2B covered the neighbouring tiles")
    add("F31", "Why the rest of the floodplain has no optical data on 2 Sep", cov.not_acquired_pct, gap,
        f"{T}/dswx_coverage_files.csv: tiles present {', '.join(present)}, no {missing[0]}; files with valid data: "
        f"{', '.join(sensors)}; share of floodplain: {T}/sep_optical_coverage.csv not_acquired_pct = "
        f"{cov.not_acquired_pct:.1f}%")
    add("F32", "…cloud or shadow", cov.cloud_pct, f"{cov.cloud_pct:.1f}%", f"{T}/sep_optical_coverage.csv: cloud_pct")
    add("F33", "NISAR coverage of the floodplain, minimum over all dates", cov.nisar_min_pct, f"{cov.nisar_min_pct:.1f}%",
        f"{T}/sep_optical_coverage.csv: nisar_min_pct")
    add("F34", "NISAR coverage of the floodplain on 3 Sep", cov.nisar_sep_pct, f"{cov.nisar_sep_pct:.1f}%",
        f"{T}/sep_optical_coverage.csv: nisar_sep_pct")
    fv = area["floodveg_km2"].max()
    add("F35", "Flooded vegetation (NISAR rule), maximum over dates", fv, f"≤ {fv:.1f} km²",
        f"{T}/area_series.csv: max(floodveg_km2)")
    add("F36", "Open water on both 17 Jul and 21 Oct (change map)", chg.loc[1, "km2"], f"{chg.loc[1, 'km2']:.0f} km²",
        f"{T}/change_20260717_20261021.csv: code 1")
    wet = float(trans[["open", "partial"]].sum().sum()) / float(trans.sum().sum())
    add("F38", "Share of the lost area (clear on 19 Jul and 8 Aug) still wet in DSWx on 8 Aug", wet, f"{100 * wet:.0f}%",
        f"{T}/jul_aug_loss_dswx_transitions.csv: (columns open + partial) / all cells")
    c0, c1 = area["ctrl90_water_pct"].iloc[0], area["ctrl90_water_pct"].iloc[-1]
    add("F39", "Permanent-water zone (JRC > 90%) classified as open water, 17 Jul / 21 Oct", (c0, c1),
        f"{c0:.1f}% on 17 Jul, {c1:.1f}% on 21 Oct", f"{T}/area_series.csv: ctrl90_water_pct, first and last row")
    lo, hi = 100 - area["ctrl90_water_pct"].max(), 100 - area["ctrl90_water_pct"].min()
    add("F40", "Share of permanent-water pixels classified as non-water on any date (range over dates)", (lo, hi),
        f"{lo:.0f}–{hi:.0f}%", f"{T}/area_series.csv: 100 − ctrl90_water_pct (min–max over the 8 dates)")
    sd0, sd1 = comp.stage_at_dswx_cm.iloc[0], comp.stage_at_dswx_cm.iloc[-1]
    add("F37", "Ladário stage at first / last DSWx date", (sd0, sd1), f"{sd0:.0f} → {sd1:.0f} cm",
        f"{T}/dswx_comparison.csv: stage_at_dswx_cm, first and last row")
    return F


QUALITATIVE = [
    ("Q1", "NISAR maps open water reliably", "F07, F09, F11"),
    ("Q2", "Open water (channel and permanent lagoons) stayed stable", "F12, F13, F36"),
    ("Q3", "The decline is in shallow, partly vegetated water (DSWx partial class)", "F14, F15"),
    ("Q4", "An L-band open-water rule does not capture that decline", "F16"),
    ("Q5", "The 17 Jul → 10 Aug NISAR drop is not water loss; consistent with vegetation emerging over shallow water",
     "F19–F24, F38 (pre-registered rule in scripts/02h_jul_aug_loss.py: > 50% on partial)"),
    ("Q6", "About a third of that drop remains unexplained; wind is not supported", "F25, F26"),
    ("Q7", "Flooded vegetation (double bounce) not detected", "F35"),
    ("Q8", "Radar backscatter alone could not map partial water (negative result)",
     "F27, F28 (pre-registered criteria in scripts/02g_partial_clf.py)"),
    ("Q9", "On 2 Sep most of the floodplain has no optical data because no HLS/DSWx product exists for tile 21KVV "
           "that day (Sentinel-2B covered the neighbouring tiles); not cloud", "F30–F32"),
    ("Q10", "Full coverage on a fixed schedule", "F05, F33, F34"),
    ("Q11", "Scattered ‘lost’/‘gained’ pixels in the main river channel are most likely classification noise near the "
            "thresholds, not channel drying", "F39, F40 (pixel-level flips between dates not computed)"),
]

WITHDRAWN = [
    ("“Radar sees through cloud and smoke in the fire season” (2 Sep example)", "F32 = 0% cloud: the optical gap was not cloud."),
    ("“The July→August drop is real / drop is real”", "Replaced by Q5 after the DSWx 8 Aug transition table (F23, F24)."),
    ("“Missed water is mostly along shorelines”", "Never measured; removed."),
    ("“Every 12 days”", "One 24-day gap (F05)."),
    ("“What dried out were marshes…” (causal wording)", "Softened to “consistent with drying of shallow, partly vegetated water”."),
    ("“Wind is ruled out”", "Softened to “wind is not supported” (F26 is a test against one rule, not proof)."),
    ("“Not imaged / not acquired that day” (2 Sep)", "Per-file check: the gap is one missing HLS/DSWx tile, 21KVV (F31)."),
    ("“Cloud-free pixels”", "Renamed “valid (clear)”: DSWx codes 0/1/2, which also excludes missing products."),
    ("“Adapted from Evans et al. 2010”; “flooded forest ≈ −4 dB”; “vegetated ≈ −23 dB” as an HH value",
     "Values not found as cited; replaced by verified Evans (2013) values for open and vegetated lakes."),
    ("“Only Landsat-9 pair” note in the wind verdict", "After completing the DSWx tiles the 19 Jul pair is L9+S2C; note removed."),
]


def agreement_figure(root: Path) -> str:
    """Same rule as scripts/02e_dswx_compare.py: the pair with the highest clear share."""
    agr = pd.read_csv(Path(root) / T / "dswx_agreement_all_pairs.csv", dtype={"nisar_date": str, "dswx_date": str})
    b = agr.sort_values("clear_pct", ascending=False).iloc[0]
    return f"outputs/figures/agreement_{b.nisar_date}_dswx_{b.dswx_date}.png"


def channel_note(F: dict) -> str:
    """Note shown under the change map (web); numbers F39, F40."""
    return ("In the main river channel, scattered ‘lost’/‘gained’ pixels are most likely classification noise near the "
            "thresholds, not channel drying: in the permanent-water zone (JRC occurrence > 90%), "
            f"{F['F40']['shown']} of pixels are classified as non-water on any date "
            f"({F['F39']['shown'].replace('% on', '% classified as water on', 1)}).")


def agreement_pair(root: Path):
    """Row of the pair shown in the agreement map (same rule as 02e: highest clear share)."""
    agr = pd.read_csv(Path(root) / T / "dswx_agreement_all_pairs.csv", dtype={"nisar_date": str, "dswx_date": str})
    return agr.sort_values("clear_pct", ascending=False).iloc[0]
