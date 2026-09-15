# KOVA Canonical Architecture

KOVA is one logical system. This repository is the canonical code source for the KOVA Operating System, KOVA AI Assistant, dashboard, MCP/integrations, automation, documentation, and deployment configuration.

## Canonical naming
- KOVA OS — complete operating system and orchestration layer
- KOVA AI Assistant — conversational/agent interface
- KOVA Dashboard — web control center
- KOVA MCP — MCP servers, clients, connectors, and tools
- KOVA Automations — scheduled/event-driven workflows
- KOVA Data — schemas, indexes, metadata, and synchronization logic

Historical spellings such as K9VA, Kiva, and Kova AI should be treated as KOVA when they refer to this project. Do not create duplicate physical folders merely to mirror naming variants.

## Canonical web namespace
Primary domain: `kovaos.com`

Preferred routes/subdomains should be documented and deployed from this repository, for example:
- `kovaos.com` — main KOVA site
- `kovaos.com/dashboard` — dashboard
- `kovaos.com/ai` — AI assistant entry point
- `kovaos.com/mcp` — MCP/integration documentation or service entry point
- `kovaos.com/docs` — documentation

DNS/provider configuration and credentials must never be committed to the repository. Deployment providers should read secrets from their protected environment/secret stores.

## Automation policy
1. `main` is the canonical current state.
2. GitHub Actions performs automated validation/status maintenance.
3. Releases are versioned snapshots; normal updates should not create duplicate source trees.
4. External data (Drive, ChatGPT project material, Notion, etc.) should be indexed/synchronized into canonical representations rather than blindly duplicated.
5. Secrets, passwords, recovery codes, OAuth tokens, API keys, private personal data, and credential exports must never be committed or published.

## Domain deployment
Domain configuration should be automated through the chosen deployment provider only after the provider and DNS authority are connected with appropriate scoped credentials. The repository may contain deployment configuration, but not the credentials themselves.
