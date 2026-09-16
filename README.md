# KOVA OS Core Assistant Component

Core repository for KOVA assistant/application logic plus supporting documentation and historical assets.

## Current role

This repository is the core assistant/application logic component for KOVA OS. It is not the canonical cross-repository orchestration hub and not an independently deployable KOVA system. Canonical architecture and repository roles live in [Kathrynhiggs21/Kova-ai-SYSTEM](https://github.com/Kathrynhiggs21/Kova-ai-SYSTEM).

Extend existing working code in this repository where possible. Audit historical directories before reuse and avoid bulk-copying the repository into other components.

## Directory guide

- `app/` — application experiments
- `assistant/` — assistant logic candidates
- `automation/` — workflow candidates
- `branding/` — brand assets
- `docs/` — historical and current documentation
- `ai-studio-v8-3/` — generated/experimental work requiring classification

## Development

The root package is a small Node/Jest project:

```bash
npm ci
npm test
npm run build
```

## Safety

Never commit secrets, personal exports, access tokens, or production credentials. Deployment claims in historical files are not authoritative unless recorded in the canonical repository map.

## Status

Catalogued but disabled in the KOVA runtime registry pending a content and build audit.
