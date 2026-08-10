# Paste this into the Google AI Studio Build assistant

Upgrade this app into the **Milli Miles Zoo Adventure V8.3 Card Studio** using the imported GitHub project as the code authority.

## Non-negotiable data authority

Use the current V8.3 Google Drive folder and production-control workbook as the data source. Do not use older V8.1, V8.2, V3, art-plate, full-surround, or two-stage files.

Drive master folder:
`https://drive.google.com/drive/folders/1d5NuuIIyxWw0cX5DdY3X8zUF49ZgSVIP`

Current V8.3 folder inside it:
`MILLI_MILES_ZOO_V8_3`

Production-control workbook:
`ZOO_V8_3_PRODUCTION_CONTROL_CENTER`

Preferred sheet/tab:
`Manus Direct Prompts`

If Google Workspace/Drive integration is available in Build mode, connect it and add a **Refresh from V8.3 Drive** action that reads the current direct-prompt rows. Keep the CSV upload fallback already in the app.

Do not store user credentials, passwords, OAuth refresh tokens, or Gemini API keys in source code. Keep Gemini calls server-side using AI Studio Secrets.

## V8.3 generation method

- One complete finished 5:7 card per generation job.
- No blank first image.
- No text-free art plate.
- No two-stage compositor.
- Exact common name, scientific name, stats, fact, category icon, subject identifier, plaque and canonical ID must all be present in the delivered image.
- Generate one card independently from every other card. Do not keep image-model chat state between cards.
- Batch queue may contain many cards, but execute each as a fresh isolated request and stop on the first failure or BLOCKED row.

## Visual lock

- Accurate hero subject, large and sharp.
- Only the distant habitat may have restrained depth-of-field blur.
- Foreground natural framing, panels, plaque, text and defining anatomy remain crisp and separated.
- Organic frame is habitat-specific and radically asymmetric.
- At least one major edge/corner remains open so real habitat reaches full bleed.
- Never make a full rectangular nature frame, vine cage, mirrored sides, equal corners, wreath, oval enclosure, reusable frame silhouette or equal-width border.
- Pop color is localized exterior accent only. Prefer a recognizable subject-derived natural color; use habitat-derived color only when the subject does not give a useful accent or contrast.
- One dominant pop-color opening; optional much smaller secondary trace. Other edges may have no pop color.
- No four-sided surround, color on every edge, grunge, speckles, splatter, peeling paint, brush smear, paper perimeter, glow, halo, ombre, fade or dissipation.
- Title panel and lower information panel use exactly the same physical material treatment. Number plaque stays in the same material family.
- Title: straight ALL CAPS, approximately 80% refined Red Panda carved-serif character and 20% Fennec Fox hand-carved softness.
- Lower panel follows Fennec Fox hierarchy.
- No footer.

## Identity and reference safety

Reference images may guide only the purpose assigned to them. Never copy a reference subject, printed ID, fact, scientific name, icon, or identifier onto another card.

Add a visible **Reference Isolation** panel showing exactly which images will be sent with the selected card. Require explicit confirmation when the selected card subject does not match the subject shown in a named subject reference. Include a **Clear references after each generation** setting, ON by default.

Add automatic prompt checks for obvious contamination terms. Example: if the selected card is BLACK-AND-WHITE COLOBUS and the assembled input includes `RED FOX`, `Vulpes vulpes`, or fox-only subject instructions, block generation and explain why.

## QA UI

For every card show these gates before Generate:

1. canonical ID/subject match
2. exact copy present
3. final category-icon instruction present
4. final subject-identifier instruction present
5. habitat-frame instruction specific, not generic
6. pop-color placement selective, not surround
7. matching material system
8. plaque/ID once only
9. no legacy two-stage tokens

After generation provide PASS / FAIL buttons for:

- identity
- anatomy
- frame asymmetry
- habitat-to-edge opening
- localized pop color
- no grunge/speckles
- panel material match
- text accuracy
- correct separate category icon and subject identifier
- plaque and ID once only
- thumbnail readability

Batch generation must not continue past a failed QA card unless the user explicitly overrides it.

## Production dashboard

Add counters for:

- total loaded
- ready
- blocked
- generated
- QA passed
- QA failed
- remaining

Add filters for category, ID range, status, generated state and QA state. Add export of a JSON/CSV run manifest with model, date, prompt hash, references used, result filename and QA status.

Preserve the current app's simple workflow and make the UI practical rather than decorative.
