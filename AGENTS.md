# KOVA OS — Repository Instructions

## Repository role

This repository is **a disabled legacy assistant and application migration source**. Its role is governed by `kova_repos_config.json` in [Kathrynhiggs21/Kova-ai-SYSTEM](https://github.com/Kathrynhiggs21/Kova-ai-SYSTEM).

`Kova-ai-SYSTEM` is the canonical orchestration hub and backend. `kovaos-site` is the canonical authenticated web application for `kovaos.com`. Read the hub's `AGENTS.md` and `docs/architecture/KOVA_REPOSITORY_MAP.md` before changing cross-repository boundaries.

## Working rules

1. Inspect the current implementation, README, registry role, and checks before changing anything.
2. Keep useful donor code and history. Migrate through reviewed changes to the canonical repository; do not deploy or promote this repository without an explicit registry decision.
3. Extend existing components. Do not create another control plane, dashboard, assistant, authentication layer, or document store.
4. Use a task branch and pull request. Review changes and run the existing relevant checks before merging; do not push unreviewed changes directly to `main`.
5. Keep normal operation no-code for the owner, and user-facing output dyslexia-first and accessibility-first.
6. Keep one canonical home per artifact. Link to canonical records rather than mirroring files. Keep KOVA AI World separate from KOVA Core.
7. Never commit or print credentials, tokens, recovery codes, private records, or secret values. Use server-side environment variables and safe templates.
8. Do not delete projects, move production domains, overwrite production environment variables, or irreversibly unlink integrations without the owner's final check.
9. Report only what a current test or runtime read proves. A passing build does not prove a deployment, authentication, or provider connection works.

## Merge automation

This repository has no approved Mergify merge queue. Do not add copied check names, blanket auto-merge rules, or configurations that queue a `do-not-merge` pull request. Use reviewed manual merges and the checks appropriate to the implementation. Production deployment ownership remains with the canonical repositories.

## Completion

Run relevant existing checks, update the canonical documentation when behavior changes, and state any credentials, permissions, or owner decisions that still block completion.
