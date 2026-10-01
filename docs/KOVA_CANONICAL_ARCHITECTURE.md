# KOVA Repository Boundary

This repository is a **disabled legacy assistant and application migration source**. The current machine-readable authority is `kova_repos_config.json` in [Kathrynhiggs21/Kova-ai-SYSTEM](https://github.com/Kathrynhiggs21/Kova-ai-SYSTEM).

## Canonical ownership

| Component | Canonical repository |
| --- | --- |
| Orchestration, backend, architecture, and cross-repository registry | `Kathrynhiggs21/Kova-ai-SYSTEM` |
| Authenticated web application and production routes for `kovaos.com` | `Kathrynhiggs21/kovaos-site` |
| Legacy assistant code in this repository | Disabled migration source; promote only by explicit registry decision |

Read the hub's `AGENTS.md` and `docs/architecture/KOVA_REPOSITORY_MAP.md` before changing these boundaries. Historical instructions calling this repository the canonical KOVA code source or telling it to deploy the production domain are superseded.

## Migration and automation

Preserve useful code and history. Migrate reviewed features into the canonical repositories instead of building another KOVA dashboard or control plane. The root Node tests and build validate the legacy root entrypoint; they do not prove any nested project or deployed provider connection works.

Use reviewed manual merges and actual implementation checks. This migration source has no approved Mergify merge queue. Keep one canonical home per artifact and sync links, identifiers, metadata, and status rather than mirroring files. Keep KOVA AI World separate from KOVA Core.

Never commit credentials, private records, recovery codes, or provider tokens. Domain reassignment, production environment overwrites, deletion, and irreversible integration unlinking require the owner's final check in the provider console.
