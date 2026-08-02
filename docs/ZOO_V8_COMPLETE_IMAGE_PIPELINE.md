# Zoo V8 Complete Image Pipeline

## Purpose

This workflow replaces the prompt-only dry run with a complete, testable image-production flow.

It uses the canonical 517-card inventory and the verified species database as separate source authorities. The source snapshots are stored in compressed bootstrap parts under `data/bootstrap/` and are automatically reconstructed at the beginning of every workflow run.

## Pipeline stages

1. Materialize the canonical production and verified species CSV files.
2. Join species facts onto the 517-card inventory by canonical card ID.
3. Reject duplicate IDs and identify incomplete records.
4. Resolve V8 pop-color, title, information-panel, contrast, identifier, and plaque rules.
5. Create an art plate:
   - `mock` mode creates a deterministic preview image without Gemini charges.
   - `gemini` mode creates the production art plate with the repository's `GEMINI_API_KEY`.
6. Apply exact text, icons, identifiers, and card numbers with the deterministic compositor.
7. Export the final master, app image, and thumbnail.
8. Validate dimensions, 5:7 geometry, file presence, data readiness, and checksums.
9. Produce a contact sheet, joined-data report, run summary, and `cards-v8.json` manifest.
10. Upload every output as a GitHub Actions artifact.

## Generated files per card

- `renders/v8/art_plates/<ID>_<SUBJECT>_V8_art_plate.png` — 2250 × 3150 PNG
- `renders/v8/masters/<ID>_<SUBJECT>_V8_master.png` — 2250 × 3150 PNG
- `renders/v8/app/<ID>_<SUBJECT>_V8.webp` — 1000 × 1400 WebP
- `renders/v8/thumbnails/<ID>_<SUBJECT>_V8_thumb.webp` — 360 × 504 WebP

## Generated reports

- `reports/v8/zoo_v8_joined_data.csv`
- `reports/v8/data_preflight_summary.json`
- `reports/v8/run_summary.json`
- `reports/v8/cards-v8.json`
- `reports/v8/contact_sheet_v8.jpg`

## Safety controls

- Pull requests always run four cards in `mock` mode and cannot incur Gemini image-generation charges.
- The default manual mode is also `mock`.
- `gemini` mode requires a configured `GEMINI_API_KEY`.
- Paid generation is blocked when a selected card has incomplete required data.
- Existing approved assets are preserved unless `overwrite` is enabled.
- No final text is requested from Gemini; exact lettering is applied after the art plate is generated.

## Manual pilot settings

For a no-cost image-producing proof:

- generation mode: `mock`
- card IDs: `A001,A002,A011,A014`
- image size: `2K`
- concurrency: `4`
- overwrite: `true`

For the first production-art test, use one fully ready card such as `A014` with generation mode `gemini`. Review the art plate, final master, app WebP, thumbnail, contact sheet, and manifest before increasing the batch.

## Current data status

The joined source contains 517 canonical records: 499 fronts and 18 category backs. The workflow reports ready and blocked counts on every run. Blocked records remain available for research and editing but cannot enter paid generation until their required content is complete.
