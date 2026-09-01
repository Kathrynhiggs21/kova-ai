# KOVA OS — Component Repository Instructions

This repository is the **core assistant/application logic component** of KOVA OS.

Canonical orchestration and cross-repository architecture live in `Kathrynhiggs21/Kova-ai-SYSTEM`. Before changing system boundaries, integrations, deployment ownership, or creating another KOVA repo, read that repository's `AGENTS.md` and `KOVA_REPO_MAP.md`.

Rules:
1. Do not treat this repository as a separate KOVA system.
2. Extend existing working code before creating duplicate services or apps.
3. Do not commit secrets, tokens, passwords, recovery codes, or production credentials.
4. Keep changes scoped to core assistant/application logic unless the orchestration map explicitly assigns broader ownership here.
5. `kovaos.com` is the canonical KOVA domain.
6. If documentation here conflicts with the orchestration hub, treat the orchestration hub as current unless an explicit migration says otherwise.
