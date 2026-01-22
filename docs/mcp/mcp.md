# MCP (Blender Bridge)

This subdomain documents how the agent talks to Blender.

## What MCP does here

- Provides a controlled way for an external Python process to execute Python inside Blender.
- Enables: scene edits, queries, camera control, and rendering.

## Primary code locations

- Client: `src/colossus_blender/mcp_client.py`
- Addon/config: `config/`

## Core operations (conceptual)

- **execute_code(code: str)**
  - Runs a Python snippet inside Blender.
  - Used for nearly all edits and camera control.

- **get_scene_info()**
  - Returns a structured summary of objects/materials/etc.

- **render/capture** (if supported by the addon)
  - Produces images for verifier evaluation.

## Failure modes

- Blender not running or addon not enabled → connection failure.
- Exceptions in executed Blender code → surfaced as errors; should be stored in iteration feedback.

## Related docs

- Setup: docs/setup/setup.md
- Pipeline: docs/pipeline.md
