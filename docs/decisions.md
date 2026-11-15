# Decisions log

Each entry: date · decision · why · alternatives discarded.

## 2026-11-11 · Challenge: Dancing with the SARs
- **Why:** highest value for EO/SAR portfolio (CDE application), NISAR is new, L-band + InSAR align with career profile.
- **Discarded:** MODIS/VIIRS Hot Spots (very crowded, checklist-type), Earth System Trend Detective (lower SAR value).

## 2026-11-11 · Theme: floodplain drying (water), not deforestation / agriculture / subsidence
- **Why:** 2026 drought documented by official gauge data; validation available (Ladário); matches the statement (wetlands extending/retracting, polarizations, drivers).
- **Discarded:** Chaco deforestation (could not confirm 2026 clearing in AOI), W Paraná agriculture (subtle signal, weak validation), Maceió subsidence (ionosphere + coherence risk in 48 h).

## 2026-11-11 · Track 132 ascending (not 111 descending)
- **Why:** 132 is HH+HV on all checked dates; 111 is HH-only on some dates; 111 evening pass has much stronger ionosphere.

## 2026-11-12 · Date range 17 Jul → 21 Oct 2026 (+ 2 Nov if published)
- **Why:** PROVISIONAL (calibrated) products start 2026-06-17; 5 Jul acquisition is partial; covers river stage ~2.5 m → ~1.25 m.
- **Discarded:** Jan–Jun 2026 (no calibrated NISAR); mixing BETA products.

## 2026-11-12 · AOI moved north: Corumbá/Ladário → Lake Mandioré strip
- **Why:** browse-level change map (17 Jul vs 21 Oct HH) showed strongest open-water loss in the floodplain lakes north of Corumbá, little change in the original Corumbá box.
- **Kept:** Corumbá/Ladário inside (story anchor, gauge location). Urban areas masked.
- **Secondary case (optional):** large wetland SW of the river (possibly Bañados de Otuquis — unverified).

## 2026-11-12 · No ML model for classification
- **Why:** open water is bimodal in HH → threshold (Otsu) is robust; a model trained on DSWx would contaminate DSWx validation. ML listed as future work.

## 2026-11-12 · InSAR water level = stretch goal only
- **Why:** dry year → little flooded vegetation; strong ionosphere in some pairs. Base project does not depend on it.

Scouting figure (browse PNGs, not a result): [`img/scouting_change_jul17_oct21_HH.png`](img/scouting_change_jul17_oct21_HH.png) — red = dark in Jul (likely water), bright in Oct.
