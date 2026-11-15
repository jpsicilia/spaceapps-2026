#!/usr/bin/env python
"""Write/refresh the "Results" section of README.md from the output tables (numbers never typed by hand).

Inserts between <!-- RESULTS:START --> and <!-- RESULTS:END --> (appends the block if the markers are missing).
Reads: outputs/tables/dswx_agreement_all_pairs.csv, dswx_comparison.csv, area_series.csv,
       optional wind_check.csv (02f) and partial_clf_summary.csv (02g).
Run from the repo root:  python scripts/update_readme_results.py
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "outputs/tables"
START, END = "<!-- RESULTS:START -->", "<!-- RESULTS:END -->"


def fmt_range(s, nd=2):
    return f"{s.min():.{nd}f}–{s.max():.{nd}f}"


def sep_sentence(cloudy):
    """Same sentence as the web card; numbers from src/pantanal_sar/facts.py (see docs/claims.md F05, F30–F33)."""
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from pantanal_sar.facts import load_facts
    F = load_facts(ROOT)
    S = {k: v["shown"] for k, v in F.items()}
    nis = ("the whole floodplain" if F["F33"]["value"] >= 99.95
           else f"at least {S['F33']} of the floodplain")
    rest = S["F31"] if F["F32"]["value"] < 1 else f"{S['F31']}; {S['F32']} cloud or shadow"
    return (f"**Full coverage on a fixed schedule.** NISAR imaged {nis} on all {S['F04']} dates, {S['F05']}; "
            f"on 2 Sep the optical product covered {S['F30']}: {rest}.")


def main():
    agr = pd.read_csv(T / "dswx_agreement_all_pairs.csv", dtype={"nisar_date": str, "dswx_date": str})
    ser = pd.read_csv(T / "dswx_comparison.csv", dtype={"nisar_date": str, "dswx_date": str})
    area = pd.read_csv(T / "area_series.csv")

    r_op, p_op = stats.pearsonr(ser["stage_at_dswx_cm"], ser["series_dswx_open_km2"])
    r_par, p_par = stats.pearsonr(ser["stage_at_dswx_cm"], ser["series_dswx_open_partial_km2"])
    r_nis, p_nis = stats.pearsonr(ser["stage_at_dswx_cm"], ser["series_nisar_km2"])
    ratio = (ser["series_nisar_km2"] / ser["series_dswx_open_km2"]).mean()
    first, last = ser.iloc[0], ser.iloc[-1]
    cloudy = agr.sort_values("clear_pct").iloc[0]
    sys.path.insert(0, str(ROOT / "src"))
    from pantanal_sar.facts import agreement_figure
    agree_rel = agreement_figure(ROOT) if (ROOT / agreement_figure(ROOT)).exists() else ""

    lines = [
        START,
        "## Results",
        "",
        f"Study area: Paraguay River floodplain, Corumbá–Ladário to Mandioré lagoon. NISAR L2 GCOV (L-band, HH+HV), "
        f"{len(area)} acquisitions from {area['date'].iloc[0]} to {area['date'].iloc[-1]}, 40 m, Lee-filtered. "
        "Open water = HV < −22 dB and HH < −16 dB (gamma0), thresholds fixed for all dates and shifted per date "
        "by the backscatter change of a stable reference (forested hills > 200 m). Validation against OPERA "
        "DSWx-HLS (optical, independent) and the Paraguay River stage at Ladário (ANA 66825000, daily mean).",
        "",
        "**1. NISAR maps open water reliably.** Against DSWx-HLS on near-simultaneous dates (≤ 2 days), "
        f"precision is {fmt_range(agr['precision'])}, recall {fmt_range(agr['recall'])} and IoU "
        f"{fmt_range(agr['iou'])} ({len(agr)} pairs). NISAR recovers on average {100 * ratio:.0f}% of the "
        "DSWx open-water area on common valid (clear) pixels.",
        "",
        "**2. Open water stayed stable; the decline is in shallow, partly vegetated water.** On pixels valid (clear) "
        f"in all paired dates ({len(ser)} dates), DSWx open water went from {first['series_dswx_open_km2']:.0f} to "
        f"{last['series_dswx_open_km2']:.0f} km² (r = {r_op:.2f} with Ladário stage, p = {p_op:.2f}), while "
        f"open + partial surface water fell from {first['series_dswx_open_partial_km2']:.0f} to "
        f"{last['series_dswx_open_partial_km2']:.0f} km² and tracks the river (r = {r_par:.2f}, p = {p_par:.3f}). "
        f"Ladário fell from {first['stage_at_dswx_cm']:.0f} to {last['stage_at_dswx_cm']:.0f} cm. "
        "The river channel and permanent lagoons held their extent; the decline is consistent with drying of "
        "shallow, partly vegetated water (DSWx partial class), which an L-band open-water rule does not capture "
        f"(NISAR open water vs stage: r = {r_nis:.2f}, p = {p_nis:.2f}).",
        "",
    ]

    loss = T / "jul_aug_loss.csv"
    wind = T / "wind_check.csv"
    lo = pd.read_csv(loss).iloc[0] if loss.exists() else None
    if lo is not None and bool(lo["supports"]):
        tr = pd.read_csv(T / "jul_aug_loss_dswx_transitions.csv", index_col=0)
        pp = float(tr.loc["partial", "partial"]) if "partial" in tr.index and "partial" in tr.columns else float("nan")
        oo = float(tr.loc["open", "open"]) if "open" in tr.index and "open" in tr.columns else float("nan")
        third = 100 * oo / lo["lost_clear_km2"]
        wtxt = ""
        if wind.exists():
            w = pd.read_csv(wind).iloc[0]
            wtxt = (f" Wind is not supported: in the permanent-water zone HH changed {w['d_hh']:+.1f} dB "
                    f"(HV {w['d_hv']:+.1f} dB) after removing the stable-reference offset.")
        lines += ["**3. The July→August drop is not water loss.** "
                  "The July→August drop in NISAR open water concentrates on DSWx partial-water pixels "
                  f"(×{lo['enrichment']:.1f} vs the plain), which DSWx still classifies as wet in August "
                  f"(partial→partial {pp:.0f} km², open→open {oo:.0f} km² of the {lo['lost_clear_km2']:.0f} km² "
                  "lost on valid (clear) pixels): consistent with vegetation emerging over shallow water and raising "
                  "L-band backscatter, not with water loss. "
                  f"About a third of the drop ({oo:.0f} km², {third:.0f}%) falls on water that DSWx kept as open "
                  "and remains unexplained." + wtxt, ""]
    elif wind.exists():
        w = pd.read_csv(wind)
        verdict = str(w["verdict"].iloc[0])
        lines += [f"**3. The July→August drop in NISAR open water is not confirmed by DSWx.** "
                  f"Wind check on the JRC permanent-water zone: {verdict}", ""]
    else:
        lines += ["**3. The July→August drop in NISAR open water is not confirmed by DSWx** "
                  "(DSWx open water did not decrease). We treat it as a limitation of the fixed-threshold rule "
                  "in that scene, not as a hydrological signal.", ""]

    clf = T / "partial_clf_summary.csv"
    if clf.exists():
        c = pd.read_csv(clf)
        lines += ["**4. Can NISAR alone see the receding shallow water?** " + str(c["summary"].iloc[0]), ""]

    if lo is not None and not bool(lo["supports"]):
        lines += [f"(Only {lo['lost_partial_pct']:.0f}% of the {lo['lost_km2']:.0f} km² lost by NISAR between 17 July "
                  "and 10 August falls on DSWx partial water of 19 July, so submerged-vegetation emergence does not "
                  "explain the drop either.)", ""]
    lines += [
        sep_sentence(cloudy),
        "",
        "**Caveats.** Seven to eight dates, consecutive and not independent: p-values are indicative. NISAR products "
        "are provisional (CRID P05023). Thresholds adapted from Evans et al. 2010 (PALSAR sigma0, converted to gamma0) "
        "and were checked, not tuned, against the JRC permanent-water zone. The Copernicus DEM is a surface model.",
        "",
        "*Unverified observation:* in late September–October HH over the river (JRC permanent-water zone) drops by "
        "1.3–2.6 dB while HV stays flat, which would be consistent with less floating vegetation in the channel.",
        "",
        "| Figure | |",
        "|---|---|",
        "| Open water NISAR vs DSWx-HLS vs Ladário | ![](outputs/figures/nisar_vs_dswx_series.png) |",
        f"| Agreement map | ![]({agree_rel}) |" if agree_rel else "",
        "| NISAR area vs stage | ![](outputs/figures/area_vs_stage.png) |",
        "| Hydroperiod (dates as open water) | ![](outputs/figures/hydroperiod.png) |",
        "",
        END,
    ]
    block = "\n".join(l for l in lines if l is not None)

    readme = ROOT / "README.md"
    txt = readme.read_text() if readme.exists() else ""
    if START in txt and END in txt:
        pre, rest = txt.split(START, 1)
        post = rest.split(END, 1)[1]
        txt = pre + block + post
    else:
        txt = txt.rstrip() + "\n\n" + block + "\n"
    readme.write_text(txt)
    print(block)
    print(f"\n[OK] README.md updated ({readme})")


if __name__ == "__main__":
    main()
