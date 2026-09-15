# KOVA Assistant Migration Source

Mixed repository containing KOVA assistant/application experiments, automation, branding, documentation, and historical generated assets.

## Current role

This repository is a migration source, not the canonical KOVA OS hub and not an independently deployable KOVA system. Canonical architecture and repository roles live in [Kathrynhiggs21/Kova-ai-SYSTEM](https://github.com/Kathrynhiggs21/Kova-ai-SYSTEM).

Useful code should be audited directory by directory and migrated through reviewed pull requests. Do not copy the entire repository into another component: some content is historical, generated, or belongs to other projects.

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
