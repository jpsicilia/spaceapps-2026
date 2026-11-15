# Claims register

Every number and claim shown in the README, the web page, the demo slides, the demo script and the submission text, with its exact source. **Generated** by `scripts/04_build_docs.py` from `outputs/tables/` and `config/` (via `src/pantanal_sar/facts.py`): do not edit by hand.

## Numbers

| ID | Claim | Shown as | Exact value | Where it appears | Source |
|---|---|---|---|---|---|
| F01 | Ladário stage on first NISAR date | 254 cm | 254.1 | Slide 1; Script; Submission | `outputs/tables/area_series.csv: stage_cm, row date=2026-07-17` |
| F02 | Ladário stage on last NISAR date | 125 cm | 125.3 | Slide 1; Script; Submission | `outputs/tables/area_series.csv: stage_cm, row date=2026-10-21` |
| F03 | River fall between first and last NISAR date | ~1.3 m | 1.287 | Slide 1; Script; Submission | `F01 − F02` |
| F04 | Number of NISAR GCOV dates | 8 | 8 | README Results intro; Web §1 lead; Slide 2; Submission | `outputs/tables/area_series.csv: row count` |
| F05 | NISAR revisit | on a 12-day repeat (one 24-day gap, 17 Jul–10 Aug: cycle 026 not available) | — | README coverage paragraph; Web card 4, §2 lead; Slide 2; Script; Submission | `outputs/tables/area_series.csv: date (differences); cycle 026 status from docs/data_inventory.md` |
| F06 | Open-water thresholds | HV < -22 dB and HH < -16 dB | -22, -16 | README Results intro; Web §1 lead; Slide 2; Submission | `config/thresholds.yaml: water_hv_max, water_hh_max` |
| F07 | Precision of NISAR open water vs DSWx-HLS (range) | 0.92–1.00 | 0.919, 0.999 | README 1; Web card 1; Slide 3; Script; Submission | `outputs/tables/dswx_agreement_all_pairs.csv: precision (min–max)` |
| F08 | Recall (range) | 0.65–0.82 | 0.647, 0.817 | README 1; Slide 3 | `outputs/tables/dswx_agreement_all_pairs.csv: recall (min–max)` |
| F09 | IoU (range) | 0.62–0.81 | 0.618, 0.814 | README 1; Web card 1; Slide 3; Submission | `outputs/tables/dswx_agreement_all_pairs.csv: iou (min–max)` |
| F10 | Number of NISAR–DSWx pairs | 8 | 8 | README 1; Web card 1; Slide 3 | `outputs/tables/dswx_agreement_all_pairs.csv: row count` |
| F11 | Share of DSWx open-water area recovered by NISAR (mean) | 87% | 0.8669 | README 1; Slide 3; Script | `outputs/tables/dswx_comparison.csv: mean(series_nisar_km2 / series_dswx_open_km2)` |
| F12 | DSWx open water, first → last common date | 257 → 258 km² | 256.8, 257.8 | README 2; Web card 2; Slide 4; Script; Submission | `outputs/tables/dswx_comparison.csv: series_dswx_open_km2, first and last row` |
| F13 | DSWx open water vs Ladário (Pearson) | r = 0.32, p = 0.49 | 0.3178, 0.4873 | README 2; Web card 2; Slide 4 | `outputs/tables/dswx_comparison.csv: pearsonr(stage_at_dswx_cm, series_dswx_open_km2)` |
| F14 | DSWx open + partial water, first → last | 948 → 580 km² | 948.4, 579.8 | README 2; Web card 3; Slide 4; Script; Submission | `outputs/tables/dswx_comparison.csv: series_dswx_open_partial_km2, first and last row` |
| F15 | DSWx open + partial vs Ladário (Pearson) | r = 0.90, p = 0.006 | 0.8984, 0.005979 | README 2; Web card 3; Slide 4; Script; Submission | `outputs/tables/dswx_comparison.csv: pearsonr(stage_at_dswx_cm, series_dswx_open_partial_km2)` |
| F16 | NISAR open water vs Ladário (Pearson) | r = 0.25, p = 0.58 | 0.2545, 0.5818 | README 2; Slide 4 | `outputs/tables/dswx_comparison.csv: pearsonr(stage_at_dswx_cm, series_nisar_km2)` |
| F17 | Number of dates in the common cloud-free series | 7 | 7 | README 2; Slide 4 | `outputs/tables/dswx_comparison.csv: row count (pairs with ≥ 80% clear)` |
| F18 | NISAR open water 17 Jul → 10 Aug | 375 → 283 km² | 375.1, 282.8 | Slide 5 | `outputs/tables/area_series.csv: water_km2, rows 1–2` |
| F19 | NISAR open water lost 17 Jul → 10 Aug | 108 km² | 107.6 | README 3 (lost on clear pixels); Slide 5; Script | `outputs/tables/jul_aug_loss.csv: lost_km2` |
| F20 | …of which on DSWx-clear pixels | 103 km² | 103.4 | README 3; Slide 5 | `outputs/tables/jul_aug_loss.csv: lost_clear_km2` |
| F21 | Share of the loss on DSWx partial water (19 Jul) | 58% | 58.11 | Slide 5; Script | `outputs/tables/jul_aug_loss.csv: lost_partial_pct (pre-registered rule: > 50%)` |
| F22 | Partial-water enrichment on lost pixels vs plain | ×3.3 | 3.33 | README 3; Slide 5 | `outputs/tables/jul_aug_loss.csv: enrichment` |
| F23 | Lost pixels still partial water in DSWx 8 Aug | 41 km² | 41.1 | README 3; Slide 5; Script | `outputs/tables/jul_aug_loss_dswx_transitions.csv: row partial, column partial` |
| F24 | Lost pixels still open water in DSWx 8 Aug | 34 km² | 34.23 | README 3; Slide 5 | `outputs/tables/jul_aug_loss_dswx_transitions.csv: row open, column open` |
| F25 | Unexplained share of the drop | 33% (about a third) | 0.331 | README 3; Slide 5; Script | `F24 / F20` |
| F26 | Wind check: HH change in permanent water, Aug vs 17 Jul (offset-corrected) | HH +0.4 dB, HV +0.2 dB | 0.3528, 0.2222 | README 3; Slide 5 | `outputs/tables/wind_check.csv: d_hh, d_hv (pre-registered rule: ≥ +1.0 dB)` |
| F27 | Partial-water classifier: mean F1 on other dates | 0.25 (target ≥ 0.50) | 0.2535 | README 4; Web (Validation); Slide 6; Script; Submission | `outputs/tables/partial_clf_summary.csv: f1_partial_mean` |
| F28 | Partial-water classifier: series vs Ladário | r = 0.01 (target ≥ 0.70) | 0.01424 | README 4; Slide 6; Submission | `outputs/tables/partial_clf_summary.csv: r_partial` |
| F29 | Classifier partial F1 by date (range) | 0.18–0.38 | 0.184, 0.383 | Slide 6 | `outputs/tables/partial_clf_metrics.csv: f1_partial_model` |
| F30 | Optical (DSWx) coverage of the floodplain on 2 Sep | 27.5% | 27.5 | README coverage; Web card 4, §2 lead; Slide 2; Script; Submission | `outputs/tables/sep_optical_coverage.csv: clear_pct` |
| F31 | …not imaged that day | 72.5% | 72.5 | README coverage; Web §2 lead and legend; Slide 2 | `outputs/tables/sep_optical_coverage.csv: not_acquired_pct (DSWx code 255/254); per-file check: outputs/tables/dswx_coverage_files.csv` |
| F32 | …cloud or shadow | 0.0% | 0 | README coverage (only if ≥ 1%); Web §2 lead (only if ≥ 1%) | `outputs/tables/sep_optical_coverage.csv: cloud_pct` |
| F33 | NISAR coverage of the floodplain, minimum over all dates | 97.2% | 97.2 | README coverage; Web card 4; Slide 2; Submission | `outputs/tables/sep_optical_coverage.csv: nisar_min_pct` |
| F34 | NISAR coverage of the floodplain on 3 Sep | 99.6% | 99.6 | Web §2 lead | `outputs/tables/sep_optical_coverage.csv: nisar_sep_pct` |
| F35 | Flooded vegetation (NISAR rule), maximum over dates | ≤ 1.4 km² | 1.426 | Web change legend (“not detected”); Slide 6 | `outputs/tables/area_series.csv: max(floodveg_km2)` |
| F36 | Open water on both 17 Jul and 21 Oct (change map) | 269 km² | 268.9 | Claims only (supports Q2) | `outputs/tables/change_20260717_20261021.csv: code 1` |
| F37 | Ladário stage at first / last DSWx date | 253 → 124 cm | 253.1, 123.5 | README 2; Web card 2; Slide 4 | `outputs/tables/dswx_comparison.csv: stage_at_dswx_cm, first and last row` |

## Qualitative claims

| ID | Claim | Supported by | Where it appears |
|---|---|---|---|
| Q1 | NISAR maps open water reliably | F07, F09, F11 | README 1; Web card 1; Slide 3 |
| Q2 | Open water (channel and permanent lagoons) stayed stable | F12, F13, F36 | README 2; Web card 2; Slide 4; Script |
| Q3 | The decline is in shallow, partly vegetated water (DSWx partial class) | F14, F15 | README 2; Web card 3, chart note; Slide 4; Script; Submission |
| Q4 | An L-band open-water rule does not capture that decline | F16 | README 2; Slide 4 |
| Q5 | The 17 Jul → 10 Aug NISAR drop is not water loss; consistent with vegetation emerging over shallow water | F19–F24 (pre-registered rule in scripts/02h_jul_aug_loss.py: > 50% on partial) | README 3; Web change note, chart note; Slide 5; Script; Submission |
| Q6 | About a third of that drop remains unexplained; wind is not supported | F25, F26 | README 3; Slide 5 |
| Q7 | Flooded vegetation (double bounce) not detected | F35 | Web change legend; Slide 6 |
| Q8 | Radar backscatter alone could not map partial water (negative result) | F27, F28 (pre-registered criteria in scripts/02g_partial_clf.py) | README 4; Web (Validation); Slide 6; Script; Submission |
| Q9 | On 2 Sep most of the floodplain was not imaged by the optical satellites that day (not cloud) | F30–F32 | README coverage; Web §2; Slide 2 |
| Q10 | Full coverage on a fixed schedule | F05, F33, F34 | README coverage; Web card 4, §2 title; Slide 2; Submission |

## Method parameters

| Parameter | Value | Where set |
|---|---|---|
| Working resolution | 40 m (2×2 multilook of 20 m, linear power) | `scripts/01_preprocess_gcov.py --res` |
| Speckle filter | Lee 5×5, ENL 11.3 fixed for all dates | `scripts/02a_preprocess_all.sh (ENL), 01 --lee-size` |
| Floodplain mask | Copernicus DEM ≤ 135 m, OSM urban removed | `scripts/02b_calibrate.py --max-height; data/processed/masks_40m.tif` |
| Stable reference | forested hills, DEM > 200 m | `scripts/02d_stability.py STABLE_MIN_M` |
| Control zone | JRC GSW occurrence > 90%, 1-px eroded | `src/pantanal_sar/classify.py jrc_permanent_on_grid` |
| Minimum mapping unit | 1 ha (7 px) | `config/thresholds.yaml mmu_px` |
| DSWx pairing | closest date ≤ 5 days (actual ≤ 2) | `scripts/02e_dswx_compare.py MAX_DAYS` |
| Common-series filter | pairs with ≥ 80% clear | `scripts/02e_dswx_compare.py --min-clear` |

## Withdrawn or corrected claims

| Earlier wording | Why it changed |
|---|---|
| “Radar sees through cloud and smoke in the fire season” (2 Sep example) | F32 = 0% cloud: the optical gap was not cloud. |
| “The July→August drop is real / drop is real” | Replaced by Q5 after the DSWx 8 Aug transition table (F23, F24). |
| “Missed water is mostly along shorelines” | Never measured; removed. |
| “Every 12 days” | One 24-day gap (F05). |
| “What dried out were marshes…” (causal wording) | Softened to “consistent with drying of shallow, partly vegetated water”. |
| “Wind is ruled out” | Softened to “wind is not supported” (F26 is a test against one rule, not proof). |

## Not verified

- Threshold values attributed to Evans et al. (2010): the paper exists (IEEE JSTARS 3(4): 560–575); the dB values were provided by the author and should be checked against the paper's tables.
- Gauge marker position on the web map: approximate (Ladário town centre), not the official station coordinates.
- “Unverified observation” in the README (river HH drop in late Sep–Oct): interpretation not tested.
