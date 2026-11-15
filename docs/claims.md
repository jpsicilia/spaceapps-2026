# Claims register

Every number and claim shown in the README, the web page, the demo slides, the demo script and the submission text, with its exact source. **Generated** by `scripts/04_build_docs.py` from `outputs/tables/` and `config/` (via `src/pantanal_sar/facts.py`): do not edit by hand.

## Numbers

| ID | Claim | Shown as | Exact value | Where it appears | Source |
|---|---|---|---|---|---|
| F01 | Ladário stage on first NISAR date | 254 cm | 254.1 | Slide 1 (title); Script; Submission | `outputs/tables/area_series.csv: stage_cm, row date=2026-07-17` |
| F02 | Ladário stage on last NISAR date | 125 cm | 125.3 | Slide 1 (title); Script; Submission | `outputs/tables/area_series.csv: stage_cm, row date=2026-10-21` |
| F03 | River fall between first and last NISAR date | ~1.3 m | 1.287 | Slide 1 (title); Script; Submission | `F01 − F02` |
| F04 | Number of NISAR GCOV dates | 8 | 8 | README Results intro; Web §1 lead; Slide 2; Submission | `outputs/tables/area_series.csv: row count` |
| F05 | NISAR revisit | on a 12-day repeat (one 24-day gap, 17 Jul–10 Aug: cycle 026 not available) | — | README coverage paragraph; Web card 4, §2 lead; Slide 2; Script; Submission | `outputs/tables/area_series.csv: date (differences); cycle 026 status from docs/data_inventory.md` |
| F06 | Open-water thresholds | HV < -22 dB and HH < -16 dB | -22, -16 | README Results intro; Web §1 lead; Slide 2; Submission | `config/thresholds.yaml: water_hv_max, water_hh_max` |
| F07 | Precision of NISAR open water vs DSWx-HLS (range) | 0.92–1.00 | 0.919, 0.999 | README 1; Web card 1; Slide 3; Script; Submission | `outputs/tables/dswx_agreement_all_pairs.csv: precision (min–max)` |
| F08 | Recall (range) | 0.65–0.78 | 0.647, 0.784 | README 1; Slide 3 | `outputs/tables/dswx_agreement_all_pairs.csv: recall (min–max)` |
| F09 | IoU (range) | 0.62–0.78 | 0.618, 0.783 | README 1; Web card 1; Slide 3; Submission | `outputs/tables/dswx_agreement_all_pairs.csv: iou (min–max)` |
| F10 | Number of NISAR–DSWx pairs | 8 | 8 | README 1; Web card 1; Slide 3 | `outputs/tables/dswx_agreement_all_pairs.csv: row count` |
| F11 | Share of DSWx open-water area recovered by NISAR (mean) | 85% | 0.8474 | README 1; Slide 3; Script | `outputs/tables/dswx_comparison.csv: mean(series_nisar_km2 / series_dswx_open_km2)` |
| F12 | DSWx open water, first → last common date | 270 → 267 km² | 269.9, 266.8 | README 2; Web card 2; Slide 4; Script; Submission | `outputs/tables/dswx_comparison.csv: series_dswx_open_km2, first and last row` |
| F13 | DSWx open water vs Ladário (Pearson) | r = 0.11, p = 0.81 | 0.1121, 0.8108 | README 2; Web card 2; Slide 4 | `outputs/tables/dswx_comparison.csv: pearsonr(stage_at_dswx_cm, series_dswx_open_km2)` |
| F14 | DSWx open + partial water, first → last | 1001 → 603 km² | 1001, 602.7 | README 2; Web card 3; Slide 4; Script; Submission | `outputs/tables/dswx_comparison.csv: series_dswx_open_partial_km2, first and last row` |
| F15 | DSWx open + partial vs Ladário (Pearson) | r = 0.89, p = 0.008 | 0.8854, 0.008018 | README 2; Web card 3; Slide 4; Script; Submission | `outputs/tables/dswx_comparison.csv: pearsonr(stage_at_dswx_cm, series_dswx_open_partial_km2)` |
| F16 | NISAR open water vs Ladário (Pearson) | r = 0.25, p = 0.59 | 0.2462, 0.5945 | README 2; Slide 4 | `outputs/tables/dswx_comparison.csv: pearsonr(stage_at_dswx_cm, series_nisar_km2)` |
| F17 | Number of dates in the common valid (clear) series | 7 | 7 | README 2; Slide 4 | `outputs/tables/dswx_comparison.csv: row count (pairs with ≥ 80% clear)` |
| F18 | NISAR open water 17 Jul → 10 Aug | 375 → 283 km² | 375.1, 282.8 | Slide 5 | `outputs/tables/area_series.csv: water_km2, rows 1–2` |
| F19 | NISAR open water lost 17 Jul → 10 Aug | 108 km² | 107.6 | README 3 (lost on clear pixels); Slide 5; Script | `outputs/tables/jul_aug_loss.csv: lost_km2` |
| F20 | …of which on DSWx-clear pixels | 107 km² | 106.6 | README 3; Slide 5 | `outputs/tables/jul_aug_loss.csv: lost_clear_km2` |
| F21 | Share of the loss on DSWx partial water (19 Jul) | 58% | 57.5 | Slide 5; Script | `outputs/tables/jul_aug_loss.csv: lost_partial_pct (pre-registered rule: > 50%)` |
| F22 | Partial-water enrichment on lost pixels vs plain | ×3.2 | 3.23 | README 3; Slide 5 | `outputs/tables/jul_aug_loss.csv: enrichment` |
| F23 | Lost pixels still partial water in DSWx 8 Aug | 42 km² | 41.76 | README 3; Slide 5; Script | `outputs/tables/jul_aug_loss_dswx_transitions.csv: row partial, column partial` |
| F24 | Lost pixels still open water in DSWx 8 Aug | 36 km² | 35.99 | README 3; Slide 5 | `outputs/tables/jul_aug_loss_dswx_transitions.csv: row open, column open` |
| F25 | Unexplained share of the drop | 34% (about a third) | 0.3377 | README 3; Slide 5; Script | `F24 / F20` |
| F26 | Wind check: HH change in permanent water, Aug vs 17 Jul (offset-corrected) | HH +0.4 dB, HV +0.2 dB | 0.3528, 0.2222 | README 3; Slide 5 | `outputs/tables/wind_check.csv: d_hh, d_hv (pre-registered rule: ≥ +1.0 dB)` |
| F27 | Partial-water classifier: mean F1 on other dates | 0.26 (target ≥ 0.50) | 0.2562 | README 4; Web (Validation); Slide 6; Script; Submission | `outputs/tables/partial_clf_summary.csv: f1_partial_mean` |
| F28 | Partial-water classifier: series vs Ladário | r = 0.01 (target ≥ 0.70) | 0.01424 | README 4; Slide 6; Submission | `outputs/tables/partial_clf_summary.csv: r_partial` |
| F29 | Classifier partial F1 by date (range) | 0.18–0.39 | 0.184, 0.387 | Slide 6 | `outputs/tables/partial_clf_metrics.csv: f1_partial_model` |
| F30 | Optical (DSWx) valid (clear) share of the analysed floodplain on 2 Sep | 25% | 25.42 | README coverage; Web card 4, §2 lead; Slide 2; Script; Submission | `outputs/tables/dswx_agreement_all_pairs.csv: clear_pct, row dswx_date=20260902 (base: see ‘Bases’ below)` |
| F47 | Optical (DSWx) valid (clear) share on the other paired dates (range) | 87–100% on 7 of 8 paired dates | 87.29, 100 | README coverage; Web card 4, §2 lead; Slide 2; Script; Submission | `outputs/tables/dswx_agreement_all_pairs.csv: clear_pct min–max without dswx_date=20260902` |
| F31 | Why the rest of the floodplain has no optical data on 2 Sep | no HLS/DSWx product exists that day for tile 21KVV, although Sentinel-2B covered the neighbouring tiles | T21KVV | README coverage; Web card 4, §2 lead and legend; Slide 2; Script; Submission | `outputs/tables/dswx_coverage_files.csv: tiles present T21KUA, T21KUU, T21KUV, T21KVA, T21KVU, no T21KVV; files with valid data: S2B` |
| F32 | …cloud or shadow | 0.0% | 0 | README coverage (only if ≥ 1%); Web §2 lead (only if ≥ 1%) | `outputs/tables/sep_optical_coverage.csv: cloud_pct` |
| F33 | NISAR coverage of the floodplain, minimum over all dates | 97.2% | 97.2 | README coverage; Web card 4; Slide 2; Submission | `outputs/tables/sep_optical_coverage.csv: nisar_min_pct` |
| F34 | NISAR coverage of the floodplain on 3 Sep | 99.6% | 99.6 | README coverage; Web §2 lead | `outputs/tables/sep_optical_coverage.csv: nisar_sep_pct` |
| F35 | Flooded vegetation (NISAR rule), maximum over dates | ≤ 1.4 km² | 1.426 | Web change legend (“not detected”); Slide 6 | `outputs/tables/area_series.csv: max(floodveg_km2)` |
| F36 | Open water on both 17 Jul and 21 Oct (change map) | 269 km² | 268.9 | Claims only (supports Q2) | `outputs/tables/change_20260717_20261021.csv: code 1` |
| F38 | Share of the lost area (clear on 19 Jul and 8 Aug) still wet in DSWx on 8 Aug | 96% | 0.9572 | Slide 5; Script | `outputs/tables/jul_aug_loss_dswx_transitions.csv: (columns open + partial) / all cells` |
| F39 | Permanent-water zone (JRC > 90%) classified as open water, 17 Jul / 21 Oct | 91.6% on 17 Jul, 90.5% on 21 Oct | 91.61, 90.49 | Web change note | `outputs/tables/area_series.csv: ctrl90_water_pct, first and last row` |
| F40 | Share of permanent-water pixels classified as non-water on any date (range over dates) | 8–12% | 8.127, 12.24 | Web change note | `outputs/tables/area_series.csv: 100 − ctrl90_water_pct (min–max over the 8 dates)` |
| F41 | Median InSAR coherence (10→22 Aug) by DSWx class: not water / open / partial | 0.55 / 0.25 / 0.32 | 0.5517, 0.2461, 0.3216 | README extension | `outputs/tables/coherence_test.csv: kind=descriptive, median` |
| F42 | Partial-water F1 without coherence (same pixels, spatial-block CV, 22 Aug) | 0.35 | 0.3499 | README extension; Slide 6 (body and takeaway); Web card 5 | `outputs/tables/coherence_test.csv: kind=verdict, f1_partial_without` |
| F43 | Partial-water F1 with coherence (pre-registered target ≥ 0.50) | 0.45 | 0.4487 | README extension; Slide 6 (body and takeaway); Web card 5 | `outputs/tables/coherence_test.csv: kind=verdict, f1_partial (label=negative)` |
| F44 | Measured gamma0 − sigma0 offset, 17 Jul floodplain (median, GCOV rtcGammaToSigmaFactor) | +1.1 dB | 1.134 | README caveats | `outputs/tables/gamma_sigma_factor.csv: offset_median_db (−10·log10 factor; scripts/02k_gamma_sigma.py)` |
| F45 | Measured gamma0 − sigma0 offset, p2–p98 (used in the physical check) | +0.9 to +1.5 dB | 0.8757, 1.456 | README caveats; physical check | `outputs/tables/gamma_sigma_factor.csv: offset_p2_db, offset_p98_db` |
| F46 | Physical check of the water thresholds vs Evans (2013), measured offset | HH OK, HV OK | HH OK, HV OK | README caveats | `src/pantanal_sar/classify.py physical_check with F45 and config/thresholds.yaml` |
| F37 | Ladário stage at first / last DSWx date | 253 → 124 cm | 253.1, 123.5 | README 2; Web card 2; Slide 4 | `outputs/tables/dswx_comparison.csv: stage_at_dswx_cm, first and last row` |

## Qualitative claims

| ID | Claim | Supported by | Where it appears |
|---|---|---|---|
| Q1 | NISAR maps open water reliably | F07, F09, F11 | README 1; Web card 1; Slide 3 |
| Q2 | Open water (channel and permanent lagoons) stayed stable | F12, F13, F36 | README 2; Web card 2; Slide 4; Script |
| Q3 | The decline is in DSWx partial surface water (≥ 20% and < 100% open water within a 30 m pixel; JPL D-107395 Rev B, Table 4-1), not in open water | F14, F15 | README 2; Web card 3, chart note; Slide 4; Script; Submission |
| Q4 | An L-band open-water rule does not capture that decline | F16 | README 2; Slide 4 |
| Q5 | The 17 Jul → 10 Aug NISAR drop is not water loss; consistent with vegetation emerging | F19–F24, F38 (pre-registered rule in scripts/02h_jul_aug_loss.py: > 50% on partial) | README 3; Web change note, chart note; Slide 5; Script; Submission |
| Q6 | About a third of that drop remains unexplained; wind is not supported | F25, F26 | README 3; Slide 5 |
| Q7 | Flooded vegetation (double bounce) not detected | F35 | Web change legend; Slide 6 |
| Q8 | Radar backscatter alone could not map partial water (negative result) | F27, F28 (pre-registered criteria in scripts/02g_partial_clf.py) | README 4; Web (Validation); Slide 6; Script; Submission |
| Q9 | On 2 Sep most of the floodplain has no optical data because no HLS/DSWx product exists for tile 21KVV that day (Sentinel-2B covered the neighbouring tiles); not cloud | F30–F32 | README coverage; Web §2; Slide 2 |
| Q10 | Radar vs optical: NISAR imaged every date; optics most dates | F05, F30, F33, F34, F47 | README coverage; Web card 4, §2 title; Slide 2; Submission |
| Q11 | Scattered ‘lost’/‘gained’ pixels in the main river channel are most likely classification noise near the thresholds, not channel drying | F39, F40 (pixel-level flips between dates not computed) | Web change note |
| Q12 | Adding InSAR coherence did not reach the pre-registered target for partial-water mapping (exploratory: one pair, one date, spatial CV) | F41–F43 (criterion in scripts/02j_coherence.py) | README extension; Slide 6 |

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
| Open-water thresholds | HV < −22 dB and HH < −16 dB (gamma0), adapted from Evans (2013) | `config/thresholds.yaml; caps in scripts/02b_calibrate.py` |

## Bases (denominators)

Two floodplain bases are used; each shown number states which. No quantity is shown on both bases.

| Base | Definition | Used for |
|---|---|---|
| Analysed floodplain (comparison base) | pixels classified on all 8 NISAR dates (not urban, DEM ≤ 135 m) | F07–F11, F30, F47; scripts/02e_dswx_compare.py |
| Study-area floodplain (coverage base) | pixels valid on at least one NISAR date (not urban, DEM ≤ 135 m) | F33, F34 (NISAR coverage by date) and the internal table outputs/tables/sep_optical_coverage.csv (its clear_pct = 27.5% for 2 Sep is on this base and is not shown anywhere); scripts/03_export_web.py |

## Withdrawn or corrected claims

| Earlier wording | Why it changed |
|---|---|
| “Radar sees through cloud and smoke in the fire season” (2 Sep example) | F32 = 0% cloud: the optical gap was not cloud. |
| “The July→August drop is real / drop is real” | Replaced by Q5 after the DSWx 8 Aug transition table (F23, F24). |
| “Missed water is mostly along shorelines” | Never measured; removed. |
| “Every 12 days” | One 24-day gap (F05). |
| “What dried out were marshes…” (causal wording) | Softened, then reworded with the official DSWx partial-water definition (see below). |
| “Wind is ruled out” | Softened to “wind is not supported” (F26 is a test against one rule, not proof). |
| “Not imaged / not acquired that day” (2 Sep) | Per-file check: the gap is one missing HLS/DSWx tile, 21KVV (F31). |
| “Cloud-free pixels” | Renamed “valid (clear)”: DSWx codes 0/1/2, which also excludes missing products. |
| “Adapted from Evans et al. 2010”; “flooded forest ≈ −4 dB”; “vegetated ≈ −23 dB” as an HH value | Values not found as cited; replaced by verified Evans (2013) values for open and vegetated lakes. |
| “Shallow, partly vegetated water”; “shallow water”; “vegetated water” for the DSWx partial class | Depth was never measured; replaced by the official DSWx-HLS definition of partial surface water (JPL D-107395 Rev B, Table 4-1). |
| σ0 → γ0 “+0.5 to 1.5 dB” (assumption) | Replaced by the offset measured from the GCOV rtcGammaToSigmaFactor layer on 17 Jul (F44, F45). |
| “On 2 Sep the optical product covered 27.5% of the floodplain” | Same date, different base (pixels valid on any NISAR date). Replaced everywhere by 25% on the base of the paired-date comparison (F30), the same base as the 87–100% range (F47). |
| “Full coverage on a fixed schedule” (section and card title) | Renamed “Radar vs optical: every date vs most dates”. |
| “Only Landsat-9 pair” note in the wind verdict | After completing the DSWx tiles the 19 Jul pair is L9+S2C; note removed. |

## Verified against external sources

| Claim | Source | Checked by |
|---|---|---|
| Median L-band σ0 (ALOS PALSAR, Lower Nhecolândia): brackish lakes without vegetation (salinas) ≈ −23 dB HH (flood and dry season) and −30 dB HV (dry season); fresh-water lakes with floating and emergent vegetation (baías) ≈ −14 dB HH (flood and dry) and −23 dB HV — basis of the thresholds (F06) | Evans, T. L. (2013), MSc thesis, Department of Geography, University of Victoria, ch. 2, section 2.4, pp. 52–53; http://hdl.handle.net/1828/4671 | Author and coding assistant, from the thesis text |
| HH threshold (−16 dB) lies between the two classes; HV threshold (−22 dB) is close to the vegetated-lake value | F06 vs the values above; `src/pantanal_sar/classify.py` PHYS_REF, printed by `scripts/02b_calibrate.py` | Script |
| Definition of DSWx-HLS partial surface water (class 2): “an inundated area that is at least 20% and less than 100% open water”; 30 m pixels | OPERA DSWx-HLS Product Specification, JPL D-107395 Rev B, Table 4-1 (10 Jul 2024), Section 4.1, p. 10; PO.DAAC OPERA_L3_DSWX-HLS_V1 (30 m) | Coding assistant (web fetch of the PO.DAAC PDF); confirmed by the author with pdftotext |
| GCOV layer rtcGammaToSigmaFactor converts the GCOV terms from gamma0 to sigma0 | ASF NISAR GCOV documentation (nisar-docs.asf.alaska.edu/gcov); NISAR L2 GCOV Product Specification, JPL D-102274 | Coding assistant, web search; sign checked in data by scripts/02k_gamma_sigma.py (factor < 1 on flat terrain) |
| Coherence combined with backscatter for wetland classification (L-, C-, X-band, Newfoundland); temporal baseline the most influential factor for coherence in herbaceous wetlands | Mohammadimanesh et al. (2018), ISPRS J. Photogramm. Remote Sens. 142, 78–93, doi:10.1016/j.isprsjprs.2018.05.009 (abstract) | Coding assistant, web search; author to confirm |
| The Shallow Open Water class has the lowest coherence (Sentinel-1, Alberta); lower coherence in the leaf-on season | Amani et al. (2021), Remote Sens. 13, 3315, doi:10.3390/rs13163315 (abstract) | Coding assistant, web search; author to confirm |
| Open water without emergent vegetation generally lacks usable coherence; herbaceous wetlands high but variable coherence | Brisco et al. (2017), Remote Sens. 9(2), 158, doi:10.3390/rs9020158 (abstract) | Coding assistant, web search; author to confirm |
| Space-averaged sample coherence magnitude is biased toward higher values | Touzi et al. (1999), IEEE TGRS 37(1), 135–149, doi:10.1109/36.739146 (abstract) | Coding assistant, web search; author to confirm |
| Combining L-band InSAR with backscatter-based methods can improve flooded-vegetation detection; relevant for NISAR | Hübinger et al. (2026), Remote Sens. Environ. 332, 115086, doi:10.1016/j.rse.2025.115086 (abstract) | Coding assistant, web search; author to confirm |

## Not verified

- Reference value for flooded vegetation (double bounce): none verified; the flooded-vegetation check is reported as NOT VERIFIED.
- Gauge marker position on the web map: approximate (±1 km), taken from Frontiers in Water 2021 (doi:10.3389/frwa.2021.639204) by the author; not the official ANA station coordinates.
- “Unverified observation” in the README (river HH drop in late Sep–Oct): interpretation not tested.
- Coherence bias narrowing the gap between open and partial water (README extension): our interpretation of Touzi et al. (1999), not tested on our data.
