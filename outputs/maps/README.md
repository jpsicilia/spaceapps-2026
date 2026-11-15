# outputs/maps

GeoTIFF maps written by `scripts/02c_timeseries.py --normalize`:

- `change_20260717_20261021.tif` — 0 stable land, 1 open water both dates, 2 open water lost, 3 open water gained,
  4–6 flooded vegetation lost / gained / both, 255 no data.
- `hydroperiod.tif` — number of dates (of 8) classified as open water, 255 no data.

GeoTIFFs are not versioned (`*.tif` in `.gitignore`). Areas per class are in `outputs/tables/`, and the web page shows
the same maps (`web/img/change.png`, `web/img/hydroperiod.png`).
