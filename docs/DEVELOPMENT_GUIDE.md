# Development Guide

This guide describes how to contribute to the Colossus Blender MCP project and how to run tests.

## Codebase Map

- `src/colossus_blender/viga/`: The primary active developmental folder. Implements the Analysis-by-Synthesis agent.
- `src/colossus_blender/mcp_client.py`: The interface to the Blender MCP server.
- `src/colossus_blender/orchestrator.py`: The legacy D5 pattern orchestrator.
- `tests/`: Pytest suite for VIGA logic and code extraction.
- `scripts/`: Utilities for model hosting and weight downloading.

## Running Tests

We use `pytest` for all logic verification.

```bash
# General tests
pytest tests/

# Individual VIGA tests
pytest tests/test_viga_agent.py
```

## Adding New Skills

The VIGA loop depends on "skills" defined in `src/colossus_blender/viga/skills.py`.
To add a new skill (e.g., Physics simulation verification):
1.  Define the method in the `SkillLibrary` class.
2.  Implement the Blender Python code as a string (or as a call to the MCP client).
3.  Expose the skill to the `VIGAAgent`.

## Multi-Agent Integration

The project supports switching between the `VIGAAgent` and the `ColossusD5Orchestrator`.
- Use **VIGA** for high-precision 3D reconstruction and iterative refinement with visual feedback.
- Use **D5** for high-level task decomposition and multi-agent "chat" workflows.
