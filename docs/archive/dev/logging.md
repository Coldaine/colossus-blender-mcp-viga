# Logging

## Goals

- Make it easy to understand what each iteration did (plan/code/feedback).
- Preserve enough information to reproduce failures.
- Avoid leaking secrets (API keys, tokens).

## What should be logged

- Iteration number
- Model selection + endpoint (redacted if needed)
- Prompt summaries (not necessarily full prompts if sensitive)
- Extracted code block
- Blender execution result (success/error)
- Verifier feedback summary

## Where logging should live

- Agent loop: `src/colossus_blender/viga/agent.py`
- MCP operations: `src/colossus_blender/mcp_client.py`

## Future enhancement

- Add a run artifact folder (per run) containing:
  - iteration JSON
  - rendered images
  - final Blender file export
