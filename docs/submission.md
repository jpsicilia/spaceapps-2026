# Space Apps 2026 — project submission draft

> Draft for the project page. Fields marked [TODO] must be completed or checked against the 2026 submission form.
> Every number is in `docs/claims.md`.

**Project name:** Pantanal 2026: Water Leaving, Seen by Radar

**Team:** Team Pantanal (one person) — José Pablo Pérez Cicilia · [TODO: Space Apps username]

**Challenge:** Dancing with the SARs · **Local event:** Ciudad del Este, Paraguay [TODO: confirm event name]

## High-level summary

In 2026 the Paraguay River at Ladário fell ~1.3 m between July and October. Using 8 NISAR L-band radar
images, we mapped open water on the Pantanal floodplain from Corumbá–Ladário to the Mandioré lagoon and validated it
against NASA OPERA optical water maps and the river gauge. NISAR maps open water with precision 0.92–1.00. Open water
(channel and lagoons) stayed stable; the water that left was shallow, partly vegetated water, which tracks the river
(r = 0.89, p = 0.008) but is not captured by an L-band open-water rule. An interactive web page shows the change map,
hydroperiod and time series.

## Project details

**What it does.** The project turns NISAR GCOV backscatter (HH and HV) into open-water maps for eight dates
on a 12-day repeat (one 24-day gap, 17 Jul–10 Aug: cycle 026 not available), measures how open water changed, and tests the result against two independent references: OPERA
DSWx-HLS (Landsat/Sentinel-2) and the Paraguay River stage at Ladário (ANA station 66825000). Open water is
HV < -22 dB and HH < -16 dB (gamma0), adapted from Evans (2013), who reports median L-band σ0 of ≈ −23 dB HH / −30 dB HV for brackish lakes without
vegetation (salinas) and ≈ −14 dB HH / −23 dB HV for fresh-water lakes with floating or emergent vegetation (baías);
our HH threshold lies between the two classes and our HV threshold is close to the vegetated-lake value.

**Results.**
- Open water from NISAR agrees with DSWx-HLS: precision 0.92–1.00, recall 0.65–0.78, IoU 0.62–0.78 (8 pairs).
- Open water stayed stable (270 → 267 km²); open + partial water declined 1001 → 603 km² and follows the river (r = 0.89, p = 0.008).
- The July→August drop in NISAR open water concentrates on DSWx partial-water pixels (×3.2 vs the plain), which
  optics still saw wet in August: consistent with vegetation emerging over shallow water, not with water loss.
  About a third remains unexplained.
- Full coverage on a fixed schedule: NISAR imaged at least 97.2% of the floodplain on all dates, on a 12-day repeat (one 24-day gap, 17 Jul–10 Aug: cycle 026 not available);
  on 2 Sep the optical product covered 27.5%: no HLS/DSWx product exists that day for tile 21KVV, although Sentinel-2B covered the neighbouring tiles.
- Negative result, reported: a pre-registered classifier could not map partial water from backscatter alone
  (F1 0.26 (target ≥ 0.50)).

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

## References
- Evans, T. L. (2013). Habitat mapping of the Brazilian Pantanal using synthetic aperture radar imagery and object
  based image analysis. MSc thesis, Department of Geography, University of Victoria. http://hdl.handle.net/1828/4671
- Sentinel-2 data enter through HLS/DSWx (modified Copernicus Sentinel data).

## Use of artificial intelligence
An AI coding assistant (Claude, Anthropic) was used to write and debug the processing code, draft documentation,
web text and these slides, under the author's specifications and review. Scientific decisions, acceptance criteria
and checks were the author's. Full statement: `docs/ai_use.md`.

## Links
- Web: https://jpsicilia.github.io/spaceapps-2026/
- Repository: https://github.com/jpsicilia/spaceapps-2026
- Demo slides: https://github.com/jpsicilia/spaceapps-2026/blob/main/docs/demo/slides.pdf
- Demo video: [TODO, if required]
- Claims register: https://github.com/jpsicilia/spaceapps-2026/blob/main/docs/claims.md

**Tags:** [TODO] NISAR, SAR, L-band, wetlands, Pantanal, surface water, hydrology, OPERA
