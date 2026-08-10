# Milli Miles Zoo V8.3 — Google AI Studio Card App

This folder is a Google AI Studio Build-mode-compatible full-stack Node app for generating Milli Miles Zoo Adventure cards from the **V8.3 locked direct-finished-card system**.

## Authority used

The app is designed around the current V8.3 source stack:

- `00_MANUS_CONTINGENCY_LOCK_V8_3_READ_FIRST`
- `01_V8_3_DIRECT_FINISHED_CARD_DESIGN_AUTHORITY`
- `V8_3_LOCKED_DIRECT_CARD_DESIGN_SYSTEM.md`
- `ZOO_V8_3_PRODUCTION_CONTROL_CENTER` → `Manus Direct Prompts`
- `V8_3_DIRECT_FINISHED_CARD_QA_CHECKLIST.md`
- V8.3 reference-image authority: approved 33-image folder controls **pop-color placement only**

## What the app does

- Loads the V8.3 `Manus Direct Prompts` CSV.
- Validates each row before image generation.
- Generates **one complete finished card per Gemini request**.
- Sends no conversation history between cards, which prevents reference contamination from spreading across the batch.
- Lets you attach reference images explicitly for the current card only.
- Enforces the V8.3 rejection rules server-side.
- Runs a batch sequentially and **stops on the first blocked row or failed generation**.
- Keeps subject, foreground frame, panels, plaque and text crisp; only distant habitat may soften.
- Enforces selective localized pop color rather than a four-sided surround.
- Removes grunge, speckles, splatter, paint edges and forced rectangular framing.

## Google AI Studio setup

Google AI Studio Build mode supports importing an existing GitHub project. In Build mode use **Add files (+) → Import from GitHub**, select the `kova-ai` repository and this app folder/branch as your source.

AI Studio automatically keeps `GEMINI_API_KEY` as a **server-side secret** for Gemini-enabled apps. Do not place an API key in browser code or commit it to GitHub.

### Branch

`ai-studio-v8-3-app`

### App folder

`ai-studio-v8-3/`

### Run command

```bash
npm install
npm start
```

## Load all 517 cards

The app intentionally does not hardcode old V8 prompts. Export/download the current V8.3 `Manus Direct Prompts` tab as CSV and load it with the file picker. This guarantees the app uses the current canonical workbook rather than a stale copy.

Expected CSV columns include:

- `Card ID`
- `Category`
- `Subject`
- `Direct Creation Status`
- `Exact On-Card Copy`
- `Manus Direct Finished-Card Prompt`
- `Output Base Filename`

## Reference isolation

Reference images are not global. Attach only the references needed for the **current card**. After a card completes, clear/change the reference files before generating another subject if necessary.

This specifically prevents the failure mode where a Red Fox reference contaminates a Black-and-White Colobus request.

## Output geometry

Gemini image models currently expose 3:4 but not native 5:7. The app therefore:

1. requests a 3:4 image;
2. tells Gemini to keep every essential card element inside the central 95% of the canvas width;
3. performs a **geometry-only** center crop of about 2.2% from each side to reach exact 5:7.

No typography, icons, panels, plaque or other design content is composited after generation. This is format normalization only.

If a future Gemini image model supports native 5:7, change `aspect_ratio` in `server.mjs` and disable normalization.

## Recommended model

Default: `gemini-3.1-flash-image` at 2K.

For difficult cards or typography-heavy retries, use the professional image model available in your AI Studio project.

## V8.3 stop rules

Do not generate a row when:

- card ID and subject disagree;
- exact verified copy is missing;
- final icon/identifier instruction is unresolved or generic;
- the prompt contains legacy art-plate/two-stage instructions;
- the prompt requires a full perimeter pop-color field;
- subject identity is ambiguous.

## Google account access

Account sign-in and Drive authorization must be performed by the user in Google AI Studio/Google Workspace. This repository does **not** contain Google passwords, OAuth tokens, API keys, or account credentials.
