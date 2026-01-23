# Claude Context Instructions

**STOP & READ** before beginning any task.

## Documentation First
This repository enforces a strict documentation culture.

1. **Before any code change**, you must understand the architecture.
   - Read [architecture.md](architecture.md) for the high-level view.
   - Read [pipeline.md](pipeline.md) if touching the agent loop.

2. **Before editing a subdomain**, read its specific documentation.
   - Touching memory/agents? Read [viga/viga.md](viga/viga.md).
   - Touching models? Read [models/models.md](models/models.md).

3. **If you change behavior**, you must update documentation.
   - Update the relevant master doc (e.g. `skills/skills.md`).
   - Log changes in [CHANGELOG.md](CHANGELOG.md).

## Coding Standards
- **Python**: Type-hint everything.
- **Tests**: Write pytest-compatible tests for all new logic. Use `MockModel` for agent tests.
- **MCP**: When executing code in Blender, assume standard imports (`bpy`, `mathutils`) are available but check context.

## Navigation
The index is at [README.md](README.md).
