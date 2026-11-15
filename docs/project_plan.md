# Project plan

## Challenge requirements (Dancing with the SARs) → how we cover them

| Statement asks for | Our answer |
|---|---|
| Interactive application using NISAR data | Web map (MapLibre) with before/after slider, time animation, charts |
| One or more types of surface change | Floodplain drying: open water and flooded vegetation, Jul–Oct 2026 |
| Pick a study area (hometown, wetland…) | Paraguay River floodplain, Corumbá–Ladário to Lake Mandioré (Triple Frontier region) |
| Download NISAR data from resources | GCOV + GUNW, track 132 A, frame 168 |
| Supplemental optical / GIS data | DSWx-HLS, Sentinel-2, OSM urban mask, gauge data |
| Hypothesize physical drivers | Prolonged drought since 2019, below-average 2026 flood, fire season, human land use |
| Which polarizations highlight change | HH (open water dark, flooded forest double-bounce bright) vs HV (vegetation volume) |
| Future NISAR applications | Wetland monitoring, drought / fire early warning, water storage |
| Storytelling, interactive summary | Story-map web page + ~2 min video (Spanish narration, English subtitles) |
| Open-source, user-friendly | Public GitHub repo, GitHub Pages |

## Layers (build in order; finish each before starting the next)

1. **Base (MVP, target Sat 13:00 first real image in the web app)**
   - Subset GCOV to AOI, HH/HV → dB, speckle filter
   - Classification per date: open water / flooded vegetation / land (Otsu on HH + HH/HV ratio), urban + NoData masked
   - Water area time series, change maps
2. **Validation**: water area vs Ladário stage; open-water agreement vs DSWx-HLS; stable-area radiometric check (HH/HV of dry forest across dates)
3. **Hydroperiod map**: number of dates flooded per pixel
4. **Stage–area relationship**: km² of flooded area per meter of river stage
5. **L-band vs C-band**: NISAR vs Sentinel-1 RTC on 2–3 dates
6. *(stretch)* **Coherence / fire**: GUNW coherence drop vs FIRMS
7. *(stretch)* **InSAR water level under vegetation** (Alsdorf et al. 2000): ionosphere-corrected GUNW, local referencing

## Team roles

- **Data & science (Pablo):** layers 1–7, hypotheses, README
- **Web & story (teammate):** web app, design, explanatory panels, video, Space Apps project page

## Interface between roles (agreed Sat 09:00)

```
outputs/maps/YYYY-MM-DD_HH.png, _HV.png, _class.png   (same extent and size)
outputs/tables/timeseries.csv   → date, water_km2, flooded_veg_km2, ladario_stage_m
outputs/maps/stats.geojson      → AOI polygon + key numbers
outputs/maps/metadata.json      → bbox, track, dates, polarizations
```

## Timeline

| When | Milestone |
|---|---|
| Sat 09:00 | Kick-off: question, AOI, interface fixed; repo goes public |
| Sat 13:00 | First real NISAR image in the web app |
| Sat 20:00 | **Science freeze** (no new analyses, only polishing) |
| Sun 12:00 | **Feature freeze** (web) |
| Sun 18:00 | Video + summary done |
| Sun 22:00 | Project submitted (hard deadline 23:59 local) |

## Submission requirements (verify on the official guide)

- Project page and linked materials in English; video may be in Spanish with English subtitles
- Public repository with the code
- Submit on spaceappschallenge.org before 15 Nov 2026, 23:59 local time
