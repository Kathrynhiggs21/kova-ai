# Canonical V8 Data Bootstrap

These Base64 text parts contain gzip-compressed snapshots of:

- `MASTER_CARD_PRODUCTION_DATABASE.csv`
- `MASTER_SPECIES_DATABASE.csv`

`python scripts/materialize_v8_data.py` joins each ordered set of parts, validates Base64, decompresses the payload, and writes the original CSV into `data/`.

The parts are split only because the repository connector writes UTF-8 text files. They are source snapshots, not card prompts, and must remain in lexical order.
