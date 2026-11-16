> **Pre-hackathon inventory (12 Nov 2026).** Some plans and checks recorded here changed during the hackathon (e.g. 2 Sep DSWx coverage: tile 21KVV has no product that day; DSWx-S1, Sentinel-1 RTC and FIRMS were downloaded but not used; the stable reference is forested hills > 200 m). The final data, method and results are in README.md, docs/reproduce.md and docs/claims.md.

# Data inventory

Checked in ASF Vertex on 2026-11-12. Status: ✅ verified · ⏳ pending · ❌ unusable

## NISAR L2 GCOV — track 132, ascending, frame 168 (PROVISIONAL)

Acquisition ~09:41 UTC (06:41 local). Mode `2005_DHDH` = HH+HV, bandwidth 20+5 MHz. Use group `frequencyA` (20 MHz).

| Cycle | Date | Size | CRID | Status | Notes |
|---|---|---|---|---|---|
| 024 | 2026-07-05 | 1.35 GB | P05023 | ❌ | Partial acquisition, does not cover AOI |
| 025 | 2026-07-17 | 1.96 GB | P05023 | ✅ | Full frame |
| 026 | ~2026-07-29 | — | — | ❌ | Not acquired / not available |
| 027 | 2026-08-10 | 1.93 GB | P05023 | ✅ | |
| 028 | 2026-08-22 | 1.97 GB | P05023 | ✅ | |
| 029 | 2026-09-03 | 1.97 GB | P05023 | ✅ | |
| 030 | 2026-09-15 | 1.93 GB | P05023 | ✅ | GUNW 030→031 strongly affected by ionosphere |
| 031 | 2026-09-27 | 1.92 GB | P05023 | ✅ | |
| 032 | 2026-10-09 | 1.93 GB | P05023 | ✅ | |
| 033 | 2026-10-21 | 1.97 GB | P05023 | ✅ | Full frame |

✅ Downloaded and verified 2026-11-12 (Vertex cart, 8 files, 15.57 GB) in `data/raw/nisar_gcov/`: all open, HHHH + HVHV present in `frequencyA`, same CRID P05023, grid EPSG:32721 (UTM 21S), native pixel 20 m, AOI 100 % inside grid.
| 034 | 2026-11-02 | — | — | ⏳ | Only L0 RRSD on 2026-11-12; check again Fri 13 Nov |

The AOI's top-left corner falls slightly outside frame 168 → NoData, masked.

## NISAR L2 GUNW — track 132, ascending, frame 168 (HH, 20 MHz, ~2.2 GB each) — 🔎 QA read 2026-11-12

QA files (`QA_SUMMARY.csv`, `QA_STATS.h5`, `QA_REPORT.pdf`, `LATLON.png`) in `data/raw/nisar_gunw/<pair>/`; full `.h5` (2.2 GB each) ✅ downloaded 2026-11-12 for the 4 useful pairs: 07-17→08-10, 08-10→08-22, 08-22→09-03, 09-15→09-27.
All 7 pairs pass the product QA. ~40–42 % NaN in every pair = grid padding outside the swath (AOI is fully inside). `identification` group check FAILs in all pairs = metadata issue of PROVISIONAL products, not data.
Stats below are **frame-wide (~240 km), not AOI**. Phase in radians; at L-band one 2π cycle ≈ 12 cm of line-of-sight change. What matters for InSAR is the *spatial variation* of the ionosphere (std), not its mean (a constant is removed by referencing).

| Pair | Days | Coherence mean | Iono screen std (rad) | Iono range (rad) | Iono uncertainty mean (rad) | Use for layer 7 (InSAR water level) |
|---|---|---|---|---|---|---|
| 07-17 → 08-10 | 24 | 0.38 | 0.39 | 3.0 | 2.17 | Candidate: almost no ionosphere, AOI still flooded; low coherence from 24 d |
| 08-10 → 08-22 | 12 | 0.55 | 1.48 | 6.7 | 1.37 | **Best** |
| 08-22 → 09-03 | 12 | 0.59 | 3.41 | 14.8 | 1.21 | Good with ionosphere correction applied |
| 09-03 → 09-15 | 12 | 0.54 | 4.96 | 21.5 | 1.42 | Only with correction; risky |
| 09-15 → 09-27 | 12 | 0.49 | 1.59 | 7.1 | 1.62 | Candidate (earlier visual check showed many fringes → verify) |
| 09-27 → 10-09 | 12 | 0.36 | 3.23 | 14.1 | 2.29 | Discard (lowest coherence, highest uncertainty) |
| 10-09 → 10-21 | 12 | 0.46 | 5.46 | 20.0 | 1.78 | Discard (strongest ionosphere) |

Pair 07-05 → 07-17 exists but uses the excluded partial date (07-05) → not used.
Layer 6 (coherence vs fire): the three pairs covering August (fire peak) have usable coherence; coherence magnitude is far less affected by the ionosphere than phase.
Ionospheric phase screen is included but **not applied** by default.

## Track 111 descending, frame 098 (secondary, not mixed into main series)

GCOV polarization varies by date (2026-06-21 `DHDH` HH+HV; 2026-10-31 `SHSH` HH only). GUNW much noisier (evening pass, ~19:04 local). Use only as extra open-water dates if needed; never for InSAR.

## Paraguay River stage at Ladário (ANA station 66825000) — ✅ downloaded 2026-11-12

`data/external/ladario_gauge/ladario_stage_raw_telemetria.csv` — ANA telemetry web service (`ServiceANA.asmx/DadosHidrometeorologicos`), requested in 30-day chunks. Raw sub-daily records (~15 min), columns `datetime, stage_cm, discharge_m3s`.

- 15,641 rows, 2026-06-01 00:00 → 2026-11-12 14:00
- Stage range: 75–256 cm
- Cross-check against bulletins: daily means on 10 Aug (242), 28 Aug (207), 28 Sep (123) and 21 Oct (125) **match exactly** → correct station.
- Daily aggregation (`ladario_stage_daily.csv`, the file named in `config/project.yaml`) is built on day 1 inside the pipeline.

Earlier values from official ANA / SGB bulletins (kept as an independent reference):

| Date | Stage (cm) | Source |
|---|---|---|
| 2026-06-30 | 251 | CEMADEN/ANA |
| 2026-07-31 | 250 | CEMADEN/ANA |
| 2026-08-10 | 242 | ANA daily bulletin |
| 2026-08-17 | 233 | ANA daily bulletin |
| 2026-08-28 | 207 | ANA daily bulletin |
| 2026-09-04 | 185 | ANA daily bulletin |
| 2026-09-28 | 123 | ANA daily bulletin |
| 2026-10-21 | 125 | SGB bulletin (via A Crítica) |
| early Nov 2026 | ~89 | Imasul (via A Crítica) — verify |

Context: last Pantanal flood 2018, peak 5.35 m at Ladário.

## OPERA DSWx-HLS (optical water, validation) — ✅ downloaded 2026-11-12

Only band `B01_WTR`. 50 files, 15 MB, in `data/raw/opera_dswx/`. Full catalog (374 granules Jul–Oct): `data/raw/opera_dswx/catalogo_dswx_hls.csv`.
Selection: closest low-cloud date with full AOI coverage (6 MGRS tiles). Cloud % = tile-level mean; DSWx cloud mask handles the rest.

| NISAR date | DSWx date | Sensor | Δ days | Tiles | Cloud % (tile mean) |
|---|---|---|---|---|---|
| 2026-07-17 | 2026-07-19 | L9 | +2 | 6 | 14 |
| 2026-08-10 | 2026-08-08 | S2C | −2 | 6 | 8 |
| 2026-08-22 | 2026-08-23 | S2B | +1 | 6 | 0 |
| 2026-09-03 | 2026-09-02 | S2A + S2B | −1 | 8 (3+5) | 2–4 |
| 2026-09-15 | 2026-09-17 | S2C | +2 | 6 | 0 |
| 2026-09-27 | 2026-09-27 | S2C | 0 | 6 | 6 |
| 2026-10-09 | 2026-10-07 | S2C | −2 | 6 | 0 |
| 2026-10-21 | 2026-10-22 | S2B | +1 | 6 | 10 |

## OPERA RTC-S1 (Sentinel-1, C-band, VV+VH) — ✅ downloaded 2026-11-12

Track 141 on both dates (same geometry), 16 bursts each, files `_VV.tif`, `_VH.tif`, `_mask.tif`. ~440 MB total in `data/raw/sentinel1_rtc/<date>/`. Catalog: `data/raw/sentinel1_rtc/catalogo_rtc_s1.csv`.

| NISAR date | S1 date | Track | Bursts | Δ days |
|---|---|---|---|---|
| 2026-07-17 | 2026-07-15 | 141 | 16 | −2 |
| 2026-10-21 | 2026-10-19 | 141 | 16 | −2 |

Discarded: track 039 (2–7 bursts, partial AOI). Platform string for track 141 not matched by S1A/B/C regex (possibly Sentinel-1D, unverified).

## Urban mask (OpenStreetMap via Overpass) — 🟡 raw exports 2026-11-12

- `data/external/urban_mask/urban_landuse.geojson`: landuse residential/industrial/commercial/retail/military/railway/construction/garages + aerodrome + military, bbox (−19.10, −57.95, −18.90, −57.50).
- `data/external/urban_mask/urban_buildings.geojson`: buildings in same bbox (fills gaps in Ladário and south Corumbá).
- Final mask built on day 1: union → buffer ~150 m → fill holes → negative buffer.

## NASA FIRMS active fires — ✅ downloaded 2026-11-12

`data/external/firms/firms_aoi_2026-08_2026-10.csv` — AOI bbox, 2026-08-01 → 2026-10-31, API area CSV (max 5 days per request).

| Source | Detections |
|---|---|
| VIIRS NOAA-20 NRT | 61 |
| VIIRS NOAA-21 NRT | 55 |
| MODIS NRT | 2 |
| **Total** | **118** (Aug 92 · Sep 21 · Oct 5) |

Note: NOAA-20 and NOAA-21 often detect the same fire → detections ≠ fires. Fire activity inside the AOI is moderate → fire layer stays a stretch goal. Hypothesis to test on day 1: August fire peak coincides with the start of the water recession (Ladário 242 cm on 10 Aug → 207 cm on 28 Aug).

## OPERA DSWx-S1 (Sentinel-1, C-band water + inundated vegetation) — ✅ downloaded 2026-11-12

Only `B01_WTR`, in `data/raw/opera_dswx_s1/<NISAR date>/`. Classes: 0 not water, 1 open water, 3 inundated vegetation, 250 HAND mask, 251 layover/shadow, 255 no data.
The 6 MGRS tiles covering the AOI are 21KUA, 21KUU, 21KUV, 21KVA, 21KVU, 21KVV. Full-coverage DSWx-S1 only exists from **13 Sep 2026** (before that, only edge passes covering ~1.5 % of the AOI) → used for the last 4 NISAR dates only. For Jul/Aug the C-band comparison uses RTC-S1 (15 Jul).

| NISAR date | DSWx-S1 date | Δ days | AOI coverage |
|---|---|---|---|
| 2026-09-15 | 2026-09-13 | −2 | 99.7 % |
| 2026-09-27 | 2026-09-25 | −2 | 99.7 % |
| 2026-10-09 | 2026-10-07 | −2 | 99.7 % |
| 2026-10-21 | 2026-10-19 | −2 | 99.7 % |

Other full-coverage dates available if needed: 18 Sep, 30 Sep, 24 Oct, 31 Oct.

## JRC Global Surface Water v1.4 (1984–2021) — ✅ downloaded 2026-11-12

`data/external/jrc_gsw/occurrence_60W_10Sv1_4_2021.tif` (38.6 MB) and `seasonality_60W_10Sv1_4_2021.tif` (18.7 MB). Tile 60W–50W, 10S–20S.
Use: reference of permanent water. A pixel that was always water but is classified as land is flagged as suspicious (floating vegetation / camalotes), not as drying.

## Copernicus DEM GLO-30 — ✅ downloaded 2026-11-12

`data/external/dem/Copernicus_DSM_COG_10_S{18,19,20}_00_W058_00_DEM.tif` (~127 MB).

| Tile | min | median | p99 | max (m) |
|---|---|---|---|---|
| S18 | 86 | 135 | 572 | 688 |
| S19 | 76 | 91 | 412 | 908 |
| S20 | 78 | 136 | 306 | 470 |

The floodplain sits at ~76–135 m, but there are hills up to 908 m inside the AOI (likely Corumbá morrarias and Serra do Amolar near Lake Mandioré) → height mask needed on day 1; stable control zone goes on flat non-flooding forest, not on hills.

## Validated NISAR GCOV collection — 🔎 checked 2026-11-12

A new collection `NISAR_L2_GCOV_V1` (CRID P05036) exists. On 12 Nov it had only 3 granules over the AOI (track 010 D and track 111 D, cycles 034–035), **none for track 132 A / frame 168** → we keep PROVISIONAL (P05023). The Nov 2 GCOV for track 132 is not available in any collection. Re-check Saturday 09:00 with `_practica/revisar_novedades.py`.
OPERA DSWx-NI: not published yet (ARSET said November 2026).
