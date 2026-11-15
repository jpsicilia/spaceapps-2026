#!/usr/bin/env python
"""Step 4: build the audit and demo documents from the versioned tables (no raw data needed).

Writes docs/claims.md, docs/demo/slides.pdf, docs/demo/script.md, docs/submission.md.
Every number comes from src/pantanal_sar/facts.py, which reads outputs/tables/ and config/.
Run from the repo root:  python scripts/04_build_docs.py
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pantanal_sar.facts import QUALITATIVE, WITHDRAWN, agreement_figure, load_facts  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from PIL import Image  # noqa: E402

WEB = "https://jpsicilia.github.io/spaceapps-2026/"
REPO = "https://github.com/jpsicilia/spaceapps-2026"
F = load_facts(ROOT)
S = {k: v["shown"] for k, v in F.items()}
REP = S["F05"].replace("on a ", "").replace(": cycle 026 not available", "")   # "12-day repeat (one 24-day gap, 17 Jul–10 Aug)"

# where each fact is shown (README sections, web elements, slides, script, submission)
WHERE = {
    "F01": "Slide 1; Script; Submission", "F02": "Slide 1; Script; Submission", "F03": "Slide 1; Script; Submission",
    "F04": "README Results intro; Web §1 lead; Slide 2; Submission",
    "F05": "README coverage paragraph; Web card 4, §2 lead; Slide 2; Script; Submission",
    "F06": "README Results intro; Web §1 lead; Slide 2; Submission",
    "F07": "README 1; Web card 1; Slide 3; Script; Submission", "F08": "README 1; Slide 3",
    "F09": "README 1; Web card 1; Slide 3; Submission", "F10": "README 1; Web card 1; Slide 3",
    "F11": "README 1; Slide 3; Script", "F12": "README 2; Web card 2; Slide 4; Script; Submission",
    "F13": "README 2; Web card 2; Slide 4", "F14": "README 2; Web card 3; Slide 4; Script; Submission",
    "F15": "README 2; Web card 3; Slide 4; Script; Submission", "F16": "README 2; Slide 4",
    "F17": "README 2; Slide 4", "F18": "Slide 5", "F19": "README 3 (lost on clear pixels); Slide 5; Script",
    "F20": "README 3; Slide 5", "F21": "Slide 5; Script", "F22": "README 3; Slide 5",
    "F23": "README 3; Slide 5; Script", "F24": "README 3; Slide 5", "F25": "README 3; Slide 5; Script",
    "F26": "README 3; Slide 5", "F27": "README 4; Web (Validation); Slide 6; Script; Submission",
    "F28": "README 4; Slide 6; Submission", "F29": "Slide 6", "F30": "README coverage; Web card 4, §2 lead; Slide 2; Script; Submission",
    "F31": "README coverage; Web card 4, §2 lead and legend; Slide 2; Script; Submission", "F32": "README coverage (only if ≥ 1%); Web §2 lead (only if ≥ 1%)",
    "F33": "README coverage; Web card 4; Slide 2; Submission", "F34": "Web §2 lead",
    "F35": "Web change legend (“not detected”); Slide 6", "F36": "Claims only (supports Q2)",
    "F37": "README 2; Web card 2; Slide 4", "F38": "Slide 5; Script",
}
QWHERE = {"Q1": "README 1; Web card 1; Slide 3", "Q2": "README 2; Web card 2; Slide 4; Script",
          "Q3": "README 2; Web card 3, chart note; Slide 4; Script; Submission", "Q4": "README 2; Slide 4",
          "Q5": "README 3; Web change note, chart note; Slide 5; Script; Submission", "Q6": "README 3; Slide 5",
          "Q7": "Web change legend; Slide 6", "Q8": "README 4; Web (Validation); Slide 6; Script; Submission",
          "Q9": "README coverage; Web §2; Slide 2", "Q10": "README coverage; Web card 4, §2 title; Slide 2; Submission"}
METHOD = [
    ("Working resolution", "40 m (2×2 multilook of 20 m, linear power)", "scripts/01_preprocess_gcov.py --res"),
    ("Speckle filter", "Lee 5×5, ENL 11.3 fixed for all dates", "scripts/02a_preprocess_all.sh (ENL), 01 --lee-size"),
    ("Floodplain mask", "Copernicus DEM ≤ 135 m, OSM urban removed", "scripts/02b_calibrate.py --max-height; data/processed/masks_40m.tif"),
    ("Stable reference", "forested hills, DEM > 200 m", "scripts/02d_stability.py STABLE_MIN_M"),
    ("Control zone", "JRC GSW occurrence > 90%, 1-px eroded", "src/pantanal_sar/classify.py jrc_permanent_on_grid"),
    ("Minimum mapping unit", "1 ha (7 px)", "config/thresholds.yaml mmu_px"),
    ("DSWx pairing", "closest date ≤ 5 days (actual ≤ 2)", "scripts/02e_dswx_compare.py MAX_DAYS"),
    ("Common-series filter", "pairs with ≥ 80% clear", "scripts/02e_dswx_compare.py --min-clear"),
]


def fmt_val(v):
    if v is None:
        return "—"
    if isinstance(v, tuple):
        return ", ".join(f"{x:.4g}" for x in v)
    try:
        return f"{float(v):.4g}"
    except (TypeError, ValueError):
        return str(v)


# --------------------------------------------------------------------------- claims.md
def write_claims():
    L = ["# Claims register", "",
         "Every number and claim shown in the README, the web page, the demo slides, the demo script and the "
         "submission text, with its exact source. **Generated** by `scripts/04_build_docs.py` from "
         "`outputs/tables/` and `config/` (via `src/pantanal_sar/facts.py`): do not edit by hand.", "",
         "## Numbers", "", "| ID | Claim | Shown as | Exact value | Where it appears | Source |", "|---|---|---|---|---|---|"]
    for k, f in F.items():
        L.append(f"| {k} | {f['label']} | {f['shown']} | {fmt_val(f['value'])} | {WHERE.get(k, '')} | `{f['source']}` |")
    L += ["", "## Qualitative claims", "", "| ID | Claim | Supported by | Where it appears |", "|---|---|---|---|"]
    for q, c, sup in QUALITATIVE:
        L.append(f"| {q} | {c} | {sup} | {QWHERE.get(q, '')} |")
    L += ["", "## Method parameters", "", "| Parameter | Value | Where set |", "|---|---|---|"]
    L += [f"| {a} | {b} | `{c}` |" for a, b, c in METHOD]
    L += ["", "## Withdrawn or corrected claims", "", "| Earlier wording | Why it changed |", "|---|---|"]
    L += [f"| {a} | {b} |" for a, b in WITHDRAWN]
    L += ["", "## Not verified", "",
          "- Threshold values attributed to Evans et al. (2010): the paper exists (IEEE JSTARS 3(4): 560–575); the dB values "
          "were provided by the author and should be checked against the paper's tables.",
          "- Gauge marker position on the web map: approximate (Ladário town centre), not the official station coordinates.",
          "- “Unverified observation” in the README (river HH drop in late Sep–Oct): interpretation not tested.", ""]
    (ROOT / "docs/claims.md").write_text("\n".join(L))


# --------------------------------------------------------------------------- slides
NAVY, INK, MUTED, ACC = "#0b2545", "#1b2430", "#5b6675", "#0f766e"


def slide(pdf, n, title, bullets, img=None, draw=None, note=None):
    fig = plt.figure(figsize=(13.333, 7.5))
    fig.patch.set_facecolor("white")
    fig.text(0.05, 0.89, title, fontsize=30, fontweight="bold", color=NAVY, va="bottom")
    fig.add_artist(plt.Line2D([0.05, 0.95], [0.875, 0.875], color=ACC, lw=2.5))
    y = 0.80
    width = 40 if draw else (46 if img else 90)
    for b in bullets:
        lines = textwrap.wrap(b, width)
        fig.text(0.06, y, "•", fontsize=19, color=ACC, va="top")
        fig.text(0.08, y, "\n".join(lines), fontsize=17, color=INK, va="top", linespacing=1.3)
        y -= 0.052 * len(lines) + 0.035
    if note:
        fig.text(0.06, 0.10, "\n".join(textwrap.wrap(note, width + 14)), fontsize=12, color=MUTED, va="bottom")
    if img:
        im = Image.open(ROOT / img)
        ax = fig.add_axes([0.52, 0.10, 0.44, 0.74])
        ax.imshow(im)
        ax.set_axis_off()
    if draw:
        ax = fig.add_axes([0.60, 0.27, 0.32, 0.54])
        draw(ax)
    fig.text(0.05, 0.035, "Team Pantanal · NASA Space Apps Challenge 2026 · Dancing with the SARs", fontsize=11, color=MUTED)
    fig.text(0.95, 0.035, f"{n} / 7", fontsize=11, color=MUTED, ha="right")
    pdf.savefig(fig)
    plt.close(fig)


def write_slides():
    area = pd.read_csv(ROOT / "outputs/tables/area_series.csv")
    trans = pd.read_csv(ROOT / "outputs/tables/jul_aug_loss_dswx_transitions.csv", index_col=0)
    out = ROOT / "docs/demo/slides.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)

    def stage_plot(ax):
        t = pd.to_datetime(area["date"])
        ax.plot(t, area["stage_cm"], "o-", color=NAVY, lw=2.5)
        ax.set_ylabel("Paraguay River stage at Ladário (cm)", fontsize=12)
        ax.set_title("Daily mean on the 8 NISAR dates (ANA 66825000)", fontsize=12, color=MUTED)
        ax.tick_params(labelsize=11)
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    def trans_plot(ax):
        cats = ["open", "partial", "not water"]
        aug = ["open", "partial", "not water"]
        cols = {"open": "#1f4e9c", "partial": "#78b4e6", "not water": "#c9b98f"}
        left = [0, 0, 0]
        for a in aug:
            vals = [float(trans.loc[c, a]) if c in trans.index and a in trans.columns else 0 for c in cats]
            ax.barh(cats, vals, left=left, color=cols[a], label=f"8 Aug: {a}")
            left = [l + v for l, v in zip(left, vals)]
        ax.set_xlabel("km² lost by NISAR between 17 Jul and 10 Aug", fontsize=12)
        ax.set_ylabel("DSWx class on 19 Jul", fontsize=12)
        ax.legend(fontsize=11, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3,
                  title="DSWx class on 8 Aug", title_fontsize=11)
        ax.tick_params(labelsize=12)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    comp = pd.read_csv(ROOT / "outputs/tables/dswx_comparison.csv", dtype={"dswx_date": str})
    clfs = pd.read_csv(ROOT / "outputs/tables/partial_clf_series.csv", dtype={"date": str})
    FS = 14

    def style(ax, ylab):
        ax.set_ylabel(ylab, fontsize=FS)
        ax.tick_params(labelsize=FS - 1)
        ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator())
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b"))
        for sp in ("top",):
            ax.spines[sp].set_visible(False)

    def stage_twin(ax, t, y):
        a2 = ax.twinx()
        a2.plot(t, y, color="#9aa3ad", lw=2, ls=":", label="Ladário stage (cm)")
        a2.set_ylabel("Ladário stage (cm)", fontsize=FS, color="#5b6675")
        a2.tick_params(labelsize=FS - 1, colors="#5b6675")
        a2.spines["top"].set_visible(False)
        return a2

    def series_plot(ax):
        t = pd.to_datetime(comp["dswx_date"])
        ax.plot(t, comp["series_dswx_open_partial_km2"], "s--", color="#4a90c8", lw=2.5, ms=7, label="DSWx open + partial")
        ax.plot(t, comp["series_dswx_open_km2"], "s-", color="#e6550d", lw=2.5, ms=7, label="DSWx open")
        ax.plot(t, comp["series_nisar_km2"], "o-", color="#0b2545", lw=2.5, ms=7, label="NISAR open")
        style(ax, "area (km², same valid pixels)")
        a2 = stage_twin(ax, t, comp["stage_at_dswx_cm"])
        h1, l1 = ax.get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, fontsize=FS - 2, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)

    def clf_plot(ax):
        t = pd.to_datetime(clfs["date"])
        ax.plot(t, clfs["nisar_partial_km2"], "o-", color="#2ca25f", lw=2.5, ms=7, label="NISAR classifier: partial")
        td = pd.to_datetime(comp["dswx_date"])
        ax.plot(td, comp["series_dswx_open_partial_km2"] - comp["series_dswx_open_km2"], "s--", color="#4a90c8",
                lw=2.5, ms=7, label="DSWx partial (valid pixels)")
        style(ax, "partial water (km²)")
        a2 = stage_twin(ax, t, clfs["stage_cm"])
        h1, l1 = ax.get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, fontsize=FS - 2, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)

    with PdfPages(out, metadata={"CreationDate": None, "ModDate": None}) as pdf:   # byte-reproducible
        slide(pdf, 1, "The Paraguay River fell ~1.3 m",
              [f"Ladário gauge: {S['F01']} on 17 Jul → {S['F02']} on 21 Oct 2026 ({S['F03']}).",
               "Question: where, and how much, did surface water change on the floodplain, "
               "and what can L-band NISAR see of it?",
               "Study area: Corumbá–Ladário to the Mandioré lagoon (Brazil–Bolivia)."], draw=stage_plot)
        slide(pdf, 2, "Data and method",
              [f"NISAR L2 GCOV (provisional), HH + HV, {S['F04']} dates, {REP}.",
               f"40 m, Lee filter, gamma0. Open water: {S['F06']}, same for all dates; urban areas and terrain > 135 m masked.",
               "Validation: OPERA DSWx-HLS (optical) and the Ladário river gauge.",
               f"Coverage: NISAR ≥ {S['F33']} of the floodplain on every date; optics on 2 Sep: {S['F30']}, "
               f"as {S['F31']}."],
              img="outputs/figures/quicklook_20260717.png")
        slide(pdf, 3, "NISAR maps open water reliably",
              [f"Precision {S['F07']} against DSWx-HLS on {S['F10']} near-simultaneous dates.",
               f"Recall {S['F08']}; IoU {S['F09']}.",
               f"NISAR recovers {S['F11']} of the optical open-water area on common valid (clear) pixels."],
              img=agreement_figure(ROOT))
        slide(pdf, 4, "Open water stable, vegetated water declined",
              [f"DSWx open water: {S['F12']} ({S['F13']} with the river).",
               f"DSWx open + partial water: {S['F14']}, tracking the river ({S['F15']}).",
               f"Ladário over the same dates: {S['F37']}.",
               f"The L-band open-water rule does not capture this decline ({S['F16']})."],
              draw=series_plot,
              note=f"{S['F17']} dates with ≥ 80% valid (clear) pixels; dates are consecutive, so p-values are indicative.")
        slide(pdf, 5, "Jul → Aug: vegetation emerging, not water loss",
              [f"NISAR open water fell {S['F18']} ({S['F19']} lost).",
               f"{S['F21']} of the lost area was DSWx partial water on 19 Jul ({S['F22']} the plain-wide share).",
               f"Optics still saw it wet on 8 Aug ({S['F38']} of it): {S['F23']} still partial, {S['F24']} still open.",
               f"{S['F25']} remains unexplained; wind is not supported ({S['F26']})."], draw=trans_plot)
        slide(pdf, 6, "Limitations and a negative result",
              [f"Pre-registered classifier failed to map partial water from backscatter: F1 {S['F27']}; "
               f"series {S['F28']}.",
               f"Flooded vegetation (double bounce) not detected ({S['F35']}).",
               f"Only {S['F04']} dates, {REP}; not independent. Provisional NISAR products.",
               "Thresholds adapted from published PALSAR values, not tuned."],
              draw=clf_plot)
        slide(pdf, 7, "Explore it",
              [f"Interactive map and charts: {WEB}",
               f"Code, data tables and claims register: {REPO}",
               "Every number in this deck is listed with its source in docs/claims.md."],
              img="outputs/figures/change_20260717_20261021.png")
    print(f"      {out}")


# --------------------------------------------------------------------------- script.md
def write_script():
    txt = f"""# Demo script (≈ 1 min 45 s, 7 slides)

Numbers below come from `docs/claims.md` (IDs in brackets). Read at a calm pace (~140 words per minute).

**Slide 1 — The problem (15 s).** Between July and October 2026 the Paraguay River at Ladário fell about
1.3 metres, from {S['F01']} to {S['F02']} [F01–F03]. We asked: where did surface water change on the floodplain,
and what can NISAR's L-band radar see of it?

**Slide 2 — Data and method (15 s).** We used {S['F04']} NISAR images, {S['F05']} [F04, F05], at 40 metres,
with fixed thresholds, and checked them against NASA's optical water maps, OPERA DSWx-HLS, and the river gauge.
NISAR imaged at least {S['F33']} of the floodplain every time; on 2 September the optical product covered
{S['F30']}, because {S['F31']} [F30, F31, F33].

**Slide 3 — Accuracy (15 s).** When NISAR says open water, the optical maps agree: precision {S['F07']} [F07],
and NISAR recovers {S['F11']} of the optical open-water area [F11].

**Slide 4 — The finding (20 s).** The river channel and lagoons barely changed: {S['F12']} [F12].
What declined was shallow, partly vegetated water: {S['F14']}, closely following the river, {S['F15']} [F14, F15].

**Slide 5 — July to August (15 s).** Between 17 July and 10 August NISAR lost {S['F19']} of open water,
but {S['F21']} of it sat on vegetated shallow water, and most of the lost area was still wet in the optical maps in
August [F19–F24, F38]. About a third remains unexplained [F25].

**Slide 6 — Honest limits (15 s).** A pre-registered classifier could not map that vegetated water from radar
backscatter alone, F1 {S['F27']} [F27], and we report it as a negative result. Products are provisional.

**Slide 7 — Explore (10 s).** Everything is open: the interactive map, the code, and a register with the source
of every number. Thank you.
"""
    (ROOT / "docs/demo/script.md").write_text(txt)


# --------------------------------------------------------------------------- submission.md
def write_submission():
    txt = f"""# Space Apps 2026 — project submission draft

> Draft for the project page. Fields marked [TODO] must be completed or checked against the 2026 submission form.
> Every number is in `docs/claims.md`.

**Project name:** Pantanal 2026: Water Leaving, Seen by Radar

**Team:** Team Pantanal (one person) — José Pablo Pérez Cicilia · [TODO: Space Apps username]

**Challenge:** Dancing with the SARs · **Local event:** Ciudad del Este, Paraguay [TODO: confirm event name]

## High-level summary

In 2026 the Paraguay River at Ladário fell {S['F03']} between July and October. Using {S['F04']} NISAR L-band radar
images, we mapped open water on the Pantanal floodplain from Corumbá–Ladário to the Mandioré lagoon and validated it
against NASA OPERA optical water maps and the river gauge. NISAR maps open water with precision {S['F07']}. Open water
(channel and lagoons) stayed stable; the water that left was shallow, partly vegetated water, which tracks the river
({S['F15']}) but is not captured by an L-band open-water rule. An interactive web page shows the change map,
hydroperiod and time series.

## Project details

**What it does.** The project turns NISAR GCOV backscatter (HH and HV) into open-water maps for eight dates
{S['F05']}, measures how open water changed, and tests the result against two independent references: OPERA
DSWx-HLS (Landsat/Sentinel-2) and the Paraguay River stage at Ladário (ANA station 66825000).

**Results.**
- Open water from NISAR agrees with DSWx-HLS: precision {S['F07']}, recall {S['F08']}, IoU {S['F09']} ({S['F10']} pairs).
- Open water stayed stable ({S['F12']}); open + partial water declined {S['F14']} and follows the river ({S['F15']}).
- The July→August drop in NISAR open water concentrates on DSWx partial-water pixels ({S['F22']} vs the plain), which
  optics still saw wet in August: consistent with vegetation emerging over shallow water, not with water loss.
  About a third remains unexplained.
- Full coverage on a fixed schedule: NISAR imaged at least {S['F33']} of the floodplain on all dates, {S['F05']};
  on 2 Sep the optical product covered {S['F30']}: {S['F31']}.
- Negative result, reported: a pre-registered classifier could not map partial water from backscatter alone
  (F1 {S['F27']}).

**Why it matters.** The Pantanal's dry-season shallow wetlands are where fish, birds and cattle depend on water, and
they are what an open-water map misses. Knowing what L-band radar does and does not see helps design NISAR-based
wetland monitoring.

**How we built it.** Python (h5py, rasterio, numpy, scipy, scikit-learn, pandas, matplotlib), Leaflet and Chart.js for
the web page, GitHub Pages for hosting. Pipeline and order: `docs/reproduce.md`.

## Use of NASA data
- NISAR L2 GCOV (NASA/JPL–ISRO), track 132 ascending, frame 168, via the ASF DAAC — main data.
- OPERA DSWx-HLS v1 (PO.DAAC) — independent optical validation (open and partial surface water).

## Use of other space agency and open data
- Copernicus DEM GLO-30 (ESA/EU) — floodplain mask and stable reference.
- JRC Global Surface Water (Pekel et al. 2016) — permanent-water control zone.
- ANA telemetry, station 66825000 — river stage. · OpenStreetMap — urban mask.
- Sentinel-2 data enter through HLS/DSWx (modified Copernicus Sentinel data).

## Use of artificial intelligence
An AI coding assistant (Claude, Anthropic) was used to write and debug the processing code, draft documentation,
web text and these slides, under the author's specifications and review. Scientific decisions, acceptance criteria
and checks were the author's. Full statement: `docs/ai_use.md`.

## Links
- Web: {WEB}
- Repository: {REPO}
- Demo slides: {REPO}/blob/main/docs/demo/slides.pdf
- Demo video: [TODO, if required]
- Claims register: {REPO}/blob/main/docs/claims.md

**Tags:** [TODO] NISAR, SAR, L-band, wetlands, Pantanal, surface water, hydrology, OPERA
"""
    (ROOT / "docs/submission.md").write_text(txt)


if __name__ == "__main__":
    write_claims()
    write_slides()
    write_script()
    write_submission()
    print("[OK] docs/claims.md, docs/demo/slides.pdf, docs/demo/script.md, docs/submission.md")
