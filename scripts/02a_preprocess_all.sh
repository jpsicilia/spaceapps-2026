#!/usr/bin/env bash
# Step 2a: preprocess all GCOV dates with the SAME settings (fixed ENL -> comparable time series),
# then print a stack check (grid alignment + basic stats per date).
# Run from the repo root:  bash scripts/02a_preprocess_all.sh
set -uo pipefail
cd "$(dirname "$0")/.."

ENL="${ENL:-11.3}"   # estimated on 2026-07-17; fixed for all dates
DATES="20260717 20260810 20260822 20260903 20260915 20260927 20261009 20261021 20261102"

for d in $DATES; do
  if ! find data -name "*${d}*.h5" | grep -qi gcov; then
    echo "---- $d: no GCOV file, skipped"; continue
  fi
  echo "==== $d"
  python scripts/01_preprocess_gcov.py --date "$d" --enl "$ENL" | grep -E "^\[1/5\]|valid|HV dB|Saved" \
    || echo "[ERROR] $d failed"
done

echo; echo "==== STACK CHECK"
python - <<'EOF'
import glob, numpy as np, rasterio
files = sorted(glob.glob("data/processed/gcov_*_40m_db.tif"))
ref = None
print(f"{'date':9} {'rows x cols':>12} {'x0':>11} {'y0':>12} {'same grid':>9} {'valid%':>6} {'HHmed':>6} {'HVmed':>6} {'%HV<-20':>7}")
for f in files:
    with rasterio.open(f) as r:
        hh, hv = r.read(1), r.read(2)
        t, sh = r.transform, r.shape
    ref = ref or (t, sh)
    same = (t == ref[0]) and (sh == ref[1])
    v = np.isfinite(hv)
    d = f.split("_")[1]
    print(f"{d:9} {sh[0]:>5} x {sh[1]:<5} {t.c:11.1f} {t.f:12.1f} {str(same):>9} {100*v.mean():6.1f} "
          f"{np.nanmedian(hh):6.2f} {np.nanmedian(hv):6.2f} {100*np.mean(hv[v] < -20):7.2f}")
EOF
