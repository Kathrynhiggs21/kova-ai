# Zoo V8 Production Authority Stack

Use sources in this order:

1. `MASTER_CARD_PRODUCTION_DATABASE.csv` — canonical IDs, categories, card types, subjects, order, and total count.
2. `MASTER_SPECIES_DATABASE.csv` — verified biological facts where a matching canonical ID exists.
3. V8 locked visual rules — pop color, asymmetry, title, information panel, contrast, and material behavior.
4. Deterministic plaque and identifier resolvers.
5. Gemini art plate generation with no final lettering.
6. Deterministic compositor for exact text, icons, identifier, and canonical ID.
7. V8 QA, checksums, contact sheet, app exports, thumbnails, and manifest.

Do not feed the renderer with older single-stage V5/V7 full-card prompt packages. Reference images control visual treatment only and never override canonical IDs or facts.
