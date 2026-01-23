# Copilot Instructions

**STOP & READ** before beginning any task.

## Documentation First
This repository is a personal tooling repo with a “docs-first” workflow.

1. **Before any code or structure change**, read the current source of truth:
   - [MASTER_REQUIREMENTS.md](MASTER_REQUIREMENTS.md)
   - [plans/plans.md](plans/plans.md)
   - [README.md](README.md) (docs index)

2. **Before editing a subdomain**, read the subdomain master doc:
   - Models: [models/models.md](models/models.md)
   - Prompts: [prompts/prompts.md](prompts/prompts.md)
   - MCP bridge: [mcp/mcp.md](mcp/mcp.md)
   - Setup: [setup/setup.md](setup/setup.md)

3. **If you change anything user-visible**, update docs immediately:
   - Update the relevant doc(s) under `docs/`.
   - Update [CHANGELOG.md](CHANGELOG.md) under “Unreleased”.
   - If you moved/archived docs, update [README.md](README.md) (docs index).

4. **If you intentionally keep something “for inspiration”** (e.g., prompts), add/maintain a TODO in the relevant doc explaining:
   - why it is kept,
   - what it’s expected to evolve into,
   - when it should be reviewed next.

## Coding Standards
- **Python**: Type-hint everything.
- **Tests**: Write pytest-compatible tests for all new logic. Use `MockModel` for agent tests.
- **MCP**: When executing code in Blender, assume standard imports (`bpy`, `mathutils`) are available but check context.

## Navigation
The index is at [README.md](README.md).
