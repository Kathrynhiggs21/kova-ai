# V8 Image Output Contract

A successful selected-card run must have the same number of files in each card asset set:

- art plates
- final master PNGs
- app WebPs
- thumbnail WebPs
- manifest rows

Every final asset must use true 5:7 geometry:

- master: 2250 × 3150
- app: 1000 × 1400
- thumbnail: 360 × 504

The run also produces one contact sheet, one joined-data CSV, one data-preflight summary, one run summary, and one `cards-v8.json` manifest. A run with missing, duplicate, incorrectly sized, or blocked paid records fails.
