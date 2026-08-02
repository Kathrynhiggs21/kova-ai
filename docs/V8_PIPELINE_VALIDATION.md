# V8 Pipeline Validation Targets

The pull-request validation run is intentionally fixed to four representative records:

- A001 — biological front, dark material
- A002 — biological front, contrasting grayscale material
- A011 — biological front, alternate habitat treatment
- A014 — Fennec Fox biological front and lower-panel reference case

The workflow must produce, for all four records:

- art-plate PNG
- final master PNG
- app WebP
- thumbnail WebP
- contact sheet
- joined-data report
- run summary
- cards-v8 manifest

The pull-request run uses deterministic mock art and therefore has no Gemini image-generation cost. Exact text and asset packaging use the same compositor and QA stages as production mode.
