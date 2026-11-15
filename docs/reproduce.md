# Reproducing the results

Everything below runs on a laptop (tested: Ubuntu, 16 GB RAM, no GPU). Total processing time ≈ 30 min after download.

## Environment

- Python: `Python 3.14.4`
- Exact package versions: [`requirements-lock.txt`](../requirements-lock.txt) (`pip freeze` of the environment that produced the results).
- Minimal install: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

## Two levels of audit

1. **From the repository alone (no raw data):** every number in the README, the web page, the slides, the script and the
   submission is computed from versioned tables in `outputs/tables/` and `config/`. Rebuild the documents with
   `python scripts/04_build_docs.py` and `python scripts/update_readme_results.py`, and compare with
   [`docs/claims.md`](claims.md).
2. **Full re-run from raw data:** download the inputs below (≈ 17 GB) and run the pipeline in order.

## Input data (`data/` is not versioned)

Exact granules, dates and checks: [`docs/data_inventory.md`](data_inventory.md).

| Path | Content | Source |
|---|---|---|
| `data/raw/nisar_gcov/*.h5` | NISAR L2 GCOV, track 132 A, frame 168, CRID P05023, 8 dates 2026-07-17 → 2026-10-21 (cycle 026 not available) | ASF DAAC (Vertex) |
| `data/raw/opera_dswx/*_B01_WTR.tif` | OPERA DSWx-HLS v1, band B01_WTR, MGRS tiles T21KUA/KUU/KUV/KVA/KVU/KVV, dates paired with NISAR (≤ 2 days) | PO.DAAC |
| `data/external/dem/Copernicus_DSM_COG_10_S{18,19,20}_00_W058_00_DEM.tif` | Copernicus DEM GLO-30 | Copernicus / AWS open data |
| `data/external/jrc_gsw/occurrence_60W_10Sv1_4_2021.tif` | JRC Global Surface Water occurrence v1.4 | JRC |
| `data/external/urban_mask/*.geojson` | OSM urban areas and buildings (Corumbá, Ladário, Puerto Suárez) | OpenStreetMap (Overpass) |
| `data/raw/nisar_gunw/**/*20260810*20260822*.h5` | NISAR L2 GUNW pair 10→22 Aug (coherenceMagnitude), only for the exploratory step 02j | ASF DAAC |
| `data/external/ladario_gauge/ladario_stage_raw_telemetria.csv` | Ladário stage, 15-min telemetry (`datetime, stage_cm, discharge_m3s`) | ANA (station 66825000) |

Optional check of the NISAR downloads: `python scripts/verificar_descargas.py data/raw/nisar_gcov`.

## Pipeline (run from the repository root, in this order)

The numbers in the file names group the steps; **02d must run before 02c**, because 02c uses its per-date offsets.

| # | Command | Needs | Produces |
|---|---|---|---|
| 1 | `bash scripts/02a_preprocess_all.sh` (calls `01_preprocess_gcov.py` for each date, ENL 11.3) | `data/raw/nisar_gcov/`, `config/aoi.geojson` | `data/processed/gcov_<date>_40m_db.tif` (HH, HV dB), `outputs/figures/quicklook_<date>.png` |
| 2 | `python scripts/02b_calibrate.py` | GCOV 17 Jul, DEM, urban mask, JRC, gauge | `data/processed/masks_40m.tif`, `config/thresholds.yaml`, `outputs/figures/calib_hist_20260717.png`, `class_preview_20260717.png` |
| 3 | `python scripts/02d_stability.py` | GCOV all dates, masks, thresholds, gauge | `outputs/tables/stability.csv` (stable-reference offsets) |
| 4 | `python scripts/02c_timeseries.py --normalize` | GCOV, masks, thresholds, `stability.csv`, gauge, JRC | `data/processed/class_<date>.tif`, `outputs/tables/area_series.csv`, `change_20260717_20261021.csv`, `outputs/maps/*.tif`, figures |
| 5 | `python scripts/02e_dswx_compare.py` | `class_<date>.tif`, DSWx, gauge | `outputs/tables/dswx_agreement_all_pairs.csv`, `dswx_comparison.csv`, figures |
| 6 | `python scripts/02f_wind_check.py` | GCOV, masks, `stability.csv`, DSWx | `outputs/tables/wind_check.csv`, `wind_check_by_date.csv` |
| 7 | `python scripts/02g_partial_clf.py` | GCOV, masks, `stability.csv`, DSWx, gauge | `outputs/tables/partial_clf_*.csv`, figures (pre-registered, negative result) |
| 7b | `python scripts/02j_coherence.py` (exploratory, optional) | GUNW 10→22 Aug, GCOV 22 Aug, masks, `stability.csv`, DSWx 23 Aug | `outputs/tables/coherence_test.csv`, `outputs/figures/coherence_test.png` |
| 8 | `python scripts/02h_jul_aug_loss.py` | `class_<date>.tif`, DSWx | `outputs/tables/jul_aug_loss.csv`, `jul_aug_loss_dswx_transitions.csv` |
| 9 | `python scripts/02i_dswx_coverage_check.py` | DSWx 2 Sep, GCOV grid | `outputs/tables/dswx_coverage_files.csv` (per-file audit of the 2 Sep optical coverage) |
| 10 | `python scripts/03_export_web.py` | all of the above | `web/img/*`, `web/data/*.json`, `outputs/tables/sep_optical_coverage.csv` |
| 11 | `python scripts/04_build_docs.py` | `outputs/tables/`, `config/`, `outputs/figures/`, `web/img/` | `docs/claims.md`, `docs/demo/slides.pdf` (copied to `web/demo/slides.pdf`), `docs/demo/script.md`, `docs/submission.md` |
| 12 | `python scripts/update_readme_results.py` | `outputs/tables/` | Results section of `README.md` |

`scripts/00_init_repo.sh` only created the GitHub repository and is not part of the pipeline.

## Deterministic choices

Fixed thresholds (`config/thresholds.yaml`), fixed ENL (11.3), fixed seed in `02g_partial_clf.py` (42),
pre-registered decision rules in `02f`, `02g` and `02h` (written in each script's docstring before it was run).
The web page is deployed by `.github/workflows/pages.yml` on every push that changes `web/`.
