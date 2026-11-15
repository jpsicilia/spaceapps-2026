# Space Apps 2026 — project submission (copy field by field)

> One block per field of the project form, in English. Team members, team name and local event come from the
> Space Apps team page, not from this text. Every number is in `docs/claims.md`. Check the field names against the
> 2026 Project Submission Guide on the form itself before pasting.

## Project Title
Pantanal 2026: What NISAR Sees — and Misses — as the Water Leaves

## High-Level Project Summary
In 2026 the Paraguay River at Ladário fell ~1.3 m between July and October. Using 8 NISAR L-band radar
images, we mapped open water on the Pantanal floodplain from Corumbá–Ladário to the Mandioré lagoon and validated it
against NASA OPERA optical water maps (DSWx-HLS) and the river gauge. NISAR maps open water with precision 0.92–1.00.
Open water (channel and lagoons) stayed stable; the decline is in partial surface water (DSWx: ≥ 20% and < 100% open water within a 30 m pixel),
which tracks the river (r = 0.89, p = 0.008) but is not captured by an L-band open-water rule. An interactive web page shows the change map,
hydroperiod and time series, and every number is traceable to its source.

## Link to Final Project
https://jpsicilia.github.io/spaceapps-2026/

(Code, data tables and documentation: https://github.com/jpsicilia/spaceapps-2026)

## Link to Project Demo
https://jpsicilia.github.io/spaceapps-2026/demo/slides.pdf

## Project Details
**What it does.** The project turns NISAR GCOV backscatter (HH and HV) into open-water maps for 8 dates
on a 12-day repeat (one 24-day gap, 17 Jul–10 Aug: cycle 026 not available), measures how open water changed, and tests the result against two independent references: OPERA
DSWx-HLS (Landsat/Sentinel-2) and the Paraguay River stage at Ladário (ANA station 66825000). Open water is
HV < -22 dB and HH < -16 dB (gamma0), adapted from Evans (2013), who reports median L-band σ0 of ≈ −23 dB HH / −30 dB HV for brackish
lakes without vegetation (salinas) and ≈ −14 dB HH / −23 dB HV for fresh-water lakes with floating or emergent
vegetation (baías); our HH threshold lies between the two classes and our HV threshold is close to the vegetated-lake
value.

**Results.**
- Open water from NISAR agrees with DSWx-HLS: precision 0.92–1.00, recall 0.65–0.78, IoU 0.62–0.78 (8 pairs).
- Open water stayed stable (270 → 267 km²); open + partial water declined 1001 → 603 km² and follows the river (r = 0.89, p = 0.008).
  Partial surface water (DSWx-HLS class 2) is defined as “an inundated area that is at least 20% and less than 100% open water” (OPERA DSWx-HLS Product Specification, JPL D-107395 Rev B, Table 4-1): sub-pixel water such as wetlands, water with emergent vegetation or mixed shoreline pixels. Water depth is not measured.
- The July→August drop in NISAR open water concentrates on DSWx partial-water pixels (×3.2 vs the plain), which
  optics still saw wet in August: consistent with vegetation emerging, not with water loss.
  About a third remains unexplained.
- Radar vs optical, every date vs most dates: NISAR imaged at least 97.2% of the floodplain on all dates,
  on a 12-day repeat (one 24-day gap, 17 Jul–10 Aug: cycle 026 not available); optics covered 87–100% on 7 of 8 paired dates, but only 25% on 2 Sep: no HLS/DSWx product exists that day for tile 21KVV, although Sentinel-2B covered the neighbouring tiles.
- Negative result, reported: a pre-registered classifier could not map partial water from backscatter alone
  (F1 0.26 (target ≥ 0.50)).

**Why it matters.** In our study area, partial surface water covered more area than open water in July
(DSWx open + partial 1001 km² vs open 270 km²), and it is what an open-water map misses.
Knowing what L-band radar does and does not see helps design NISAR-based wetland monitoring.

**How we built it.** Python (h5py, rasterio, numpy, scipy, scikit-learn, pandas, matplotlib), Leaflet and Chart.js for
the web page, GitHub Pages for hosting. Pipeline and order: docs/reproduce.md. Claims register: docs/claims.md.

## Use of NASA Data
- NISAR L2 GCOV (NASA/JPL–ISRO, provisional), track 132 ascending, frame 168, HH and HV, 8 dates, via the ASF DAAC —
  main data.
- OPERA DSWx-HLS v1 (PO.DAAC) — independent optical validation (open and partial surface water).
- NISAR L2 GUNW (NASA/JPL–ISRO, provisional), pair 10→22 Aug 2026, coherence — exploratory test (partial-water F1 0.35 → 0.45). Limitations: labels are DSWx-HLS “partial” (optical, not field data); one pair and one date; coherence depends on temporal baseline and phenology.

## Use of Space Agency Partner Data
- Copernicus DEM GLO-30 (ESA / European Union) — floodplain mask and stable reference.
- Sentinel-2 (ESA/Copernicus) enters through HLS and DSWx-HLS (modified Copernicus Sentinel data).

## References
Data
- NISAR L2 GCOV: NASA/JPL and ISRO, distributed by the ASF DAAC.
- OPERA. 2023. OPERA Dynamic Surface Water Extent from Harmonized Landsat Sentinel-2 (Version 1). PO.DAAC.
  https://doi.org/10.5067/OPDSW-PL3V1
- Copernicus DEM GLO-30: © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS
  by the European Union and ESA.
- Pekel, J.-F., Cottam, A., Gorelick, N., Belward, A. S. (2016). High-resolution mapping of global surface water and
  its long-term changes. Nature 540, 418–422 (JRC Global Surface Water).
- ANA (Agência Nacional de Águas e Saneamento Básico), telemetry of station 66825000, Ladário.
- © OpenStreetMap contributors (ODbL): urban mask and web basemap option.

Literature
- Evans, T. L. (2013). Habitat mapping of the Brazilian Pantanal using synthetic aperture radar imagery and object
  based image analysis. MSc thesis, University of Victoria. http://hdl.handle.net/1828/4671
- Amani, M., Poncos, V., Brisco, B., Foroughnia, F., DeLancey, E. R., Ranjbar, S. (2021). InSAR coherence analysis for wetlands in Alberta, Canada using time-series Sentinel-1 data. Remote Sensing 13(16), 3315. https://doi.org/10.3390/rs13163315
- Brisco, B., Ahern, F., Murnaghan, K., White, L., Canisus, F., Lancaster, P. (2017). Seasonal change in wetland coherence as an aid to wetland monitoring. Remote Sensing 9(2), 158. https://doi.org/10.3390/rs9020158
- Hübinger, C., Fluet-Chouinard, E., Escobar, D., Jaramillo, F. (2026). Exploring the potential of using L-band InSAR for the mapping of flooded vegetation in tropical wetlands. Remote Sensing of Environment 332, 115086. https://doi.org/10.1016/j.rse.2025.115086
- Mohammadimanesh, F., Salehi, B., Mahdianpari, M., Brisco, B., Motagh, M. (2018). Multi-temporal, multi-frequency, and multi-polarization coherence and SAR backscatter analysis of wetlands. ISPRS Journal of Photogrammetry and Remote Sensing 142, 78–93. https://doi.org/10.1016/j.isprsjprs.2018.05.009
- Touzi, R., Lopes, A., Bruniquel, J., Vachon, P. W. (1999). Coherence estimation for SAR imagery. IEEE Transactions on Geoscience and Remote Sensing 37(1), 135–149. https://doi.org/10.1109/36.739146

Software and web
- Python: numpy, scipy, pandas, h5py, rasterio, pyproj, shapely, geopandas, scikit-learn, matplotlib, Pillow.
- Leaflet 1.9.4 (BSD-2-Clause), Chart.js 4.4.1 (MIT), GitHub Pages.
- Basemap: Esri World Imagery (Imagery © Esri, Maxar, Earthstar Geographics), shown with attribution.

## Use of Artificial Intelligence
An AI assistant (Claude, Anthropic) was used to write and debug the processing code and to draft the documentation,
web text and slides, from the author's specifications; a second, separate Claude chat acted as an independent
reviewer. The author approved every change and ran all the code. No data, labels, images or results were generated by
AI. Every code file carries an "AI-assisted" header. Full statement: https://github.com/jpsicilia/spaceapps-2026/blob/main/docs/ai_use.md

## Tags
NISAR, SAR, L-band, Pantanal, wetlands, surface water, flood dynamics, OPERA DSWx, hydrology, remote sensing

## Before pressing Submit
- Open both links in a private window and check they load without signing in.
- Check the box on the form agreeing to the submission requirements and the Participant Terms and Conditions.
