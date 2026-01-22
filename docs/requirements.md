# Documentation Requirements (Schema)

This project uses a documentation layout designed for separation of concerns and predictable navigation.

## 1) Root `docs/` contents

The root docs folder should contain:
- **architecture.md**: high-level components and how they connect.
- **pipeline_overview.md**: operational overview of what happens.
- **pipeline.md**: deep dive, definitive runtime description.
- **requirements.md**: *this file* (documentation schema + rules).
- **CHANGELOG.md**: human-readable change history.
- **todo.md**: tracked work items for docs/system improvements.

The root docs folder may also contain **README.md** as the documentation index.

## 2) Subdomain folders

For each subdomain, create a folder under `docs/`.

Rule: each subdomain folder MUST contain a “master doc” named exactly like the folder.

Examples:
- `docs/models/models.md`
- `docs/viga/viga.md`
- `docs/mcp/mcp.md`

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
- `claude.md`

Those files MUST:
- point to the docs index
- instruct contributors to read `docs/architecture.md` before starting work
- instruct contributors to read the subdomain docs relevant to their task
