# Documentation Requirements (Schema)

This project uses a documentation layout designed for separation of concerns and predictable navigation.

## 1) Root `docs/` contents

The root docs folder should contain:
- **MASTER_REQUIREMENTS.md**: source of truth for architecture and requirements.
- **requirements.md**: *this file* (documentation schema + rules).
- **CHANGELOG.md**: human-readable change history.

The root docs folder may also contain:
- **README.md**: documentation index.
- **copilot-instructions.md**: assistant workflow rules.

The root docs folder may also contain **archive/** to preserve legacy docs without polluting active guidance.

## 2) Subdomain folders

For each subdomain, create a folder under `docs/`.

Rule: each subdomain folder MUST contain a “master doc” named exactly like the folder.

Examples:
- `docs/models/models.md`
- `docs/mcp/mcp.md`
- `docs/prompts/prompts.md`
- `docs/setup/setup.md`
- `docs/plans/plans.md`
- `docs/status/verified_working.md`

Additional supporting docs may live alongside the master doc as needed.

## 3) Content expectations

Each master doc should cover:
- Purpose and scope of the subdomain
- “How it works” summary
- Configuration knobs (env vars, files)
- Relevant source locations
- Common failure modes and debugging tips

## 4) Linking conventions

- Prefer relative links within docs.
- If a doc is moved, update inbound links in:
  - `docs/README.md`
  - root `README.md`
  - any impacted subdomain master docs

## 5) Change management

- Any structural change to `docs/` should update:
  - `docs/README.md` (index)
  - `docs/CHANGELOG.md`
- Prefer incremental changes that can be reviewed as small PRs.

## 6) Contribution instructions

Contributor-facing instructions live in:
- `copilot-instructions.md`

Those files MUST:
- point to the docs index
- instruct contributors/assistants to read `docs/MASTER_REQUIREMENTS.md` before starting work
- instruct contributors/assistants to read the subdomain docs relevant to their task

If additional assistant-specific instruction files exist, prefer keeping them in `docs/archive/` unless they are actively used.
