# Pantanal 2026: Water Leaving, Seen by Radar

**NASA Space Apps Challenge 2026 · Challenge: _Dancing with the SARs_**
Local event: Ciudad del Este, Paraguay · Team: _[team name]_

> 🚧 Work in progress. Project development starts on **14 Nov 2026, 09:00 (local time)**, following the hackathon rules.
> Everything in this repository before that moment is planning and setup only (folder structure, environment, documentation).

## Question

Where, and how much, did the Paraguay River floodplain dry out between July and October 2026,
which NISAR polarization shows it best, and what drove it?

## Study area

Paraguay River floodplain from Corumbá / Ladário (Brazil) north to Lake Mandioré
(Brazil–Bolivia border). Bounding box (EPSG:4326):
`POLYGON((-57.95 -19.08, -57.30 -19.08, -57.30 -17.95, -57.95 -17.95, -57.95 -19.08))`

## Data

| Dataset | Use |
|---|---|
| NISAR L2 GCOV (PROVISIONAL), track 132 ascending, frame 168, HH+HV, 8 dates (17 Jul → 21 Oct 2026) | Open water / flooded vegetation mapping, hydroperiod |
| NISAR L2 GUNW (PROVISIONAL), 7 consecutive 12-day pairs | Coherence change; water-level change under vegetation (stretch goal) |
| Sentinel-1 RTC (C-band) | L-band vs C-band comparison |
| OPERA DSWx-HLS | Independent optical validation (open water only) |
| Paraguay River stage at Ladário (ANA station 66825000) | Validation and stage–area relationship |
| NASA FIRMS active fires | Fire layer validation |
| OpenStreetMap urban boundaries | Urban mask |

Full inventory: [`docs/data_inventory.md`](docs/data_inventory.md)

## Method

_To be completed during the hackathon._ Plan: [`docs/project_plan.md`](docs/project_plan.md)

## Repository structure

```
config/      study area and project settings
data/        raw / external / interim / processed (not versioned)
docs/        plan, data inventory, decisions, logbook, references
notebooks/   exploration and figures
src/         processing code
web/         interactive web application
outputs/     figures, maps, tables
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your keys
```

NASA Earthdata credentials go in `~/.netrc` (never in this repository).

## Team

- Pablo Pérez Cicilia — radar data processing, analysis, validation
- _[teammate]_ — web application, design, storytelling, video

## License

MIT. Data © NASA/JPL/ISRO (NISAR), ESA (Sentinel-1), NASA (OPERA, FIRMS), ANA (gauge data), OpenStreetMap contributors.
