# Skills

This subdomain documents the skill/tool surface the agents use.

## Purpose

Skills are the stable interface between:
- the agent loop (planning, decision-making), and
- concrete actions (Blender edits, camera motion, scene queries).

## Where it lives

- Implementation: `src/colossus_blender/viga/skills.py`

## Current skills (high level)

Generation tools:
- `make_plan(task_description, context_memory)`
- `execute_code(code)`
- `get_scene_info_text()`
- `get_better_assets(query)` (placeholder)

Verification tools:
- `initialize_viewpoint()` (frames scene by bounding box)
- `set_camera(location, rotation)`
- `investigate(instruction)` (NL camera adjustment)
- `set_visibility(object_name, visible)`

## Adding a new skill

- Keep skills small and testable.
- Prefer returning structured data (dict) where possible.
- If a skill depends on model output, enforce strict output formatting.

## Related docs

- Pipeline: docs/pipeline.md
- MCP bridge: docs/mcp/mcp.md
