# Architecture

This document describes the *high-level* components of Colossus Blender MCP and how they fit together. If you are new to the project, start here.

## Goal

Provide a closed-loop 3D modeling system where an agent:
1) proposes Blender edits (code),
2) applies them to a live Blender scene, and
3) visually verifies progress using a vision-language model (VLM),
repeating until the target spec is met.

## Core Components

### 1) Blender Runtime
- **What**: A running Blender instance containing the scene being edited.
- **Why**: Blender is the source of truth for geometry, materials, camera, rendering.
- **Assumption**: Blender is launched with the project’s MCP addon enabled.

### 2) MCP Bridge (Blender ↔ Python)
- **What**: A socket-based bridge that lets Python (outside Blender) execute Python inside Blender.
- **Where (code)**: `src/colossus_blender/mcp_client.py` and the Blender addon under `config/`.
- **Typical operations**:
  - execute a Python snippet in Blender
  - fetch basic scene info
  - (optionally) render/capture images for verification

### 3) VIGA Agent Loop (Generator ↔ Verifier)
- **What**: The main Analysis-by-Synthesis loop.
- **Where (code)**: `src/colossus_blender/viga/agent.py`
- **Parts**:
  - **GeneratorAgent**: plans + produces Blender Python edits
  - **VerifierAgent**: inspects results (scene + renders) and returns corrective feedback
  - **VIGAAgent**: orchestration of the iterative loop

### 4) Evolving Context Memory
- **What**: Stores iteration history (plan, code, verification feedback) with a sliding window.
- **Where (code)**: `src/colossus_blender/viga/memory.py`
- **Why**: Keeps the loop grounded without blowing token/context limits.

### 5) Skill Library (Tooling Surface)
- **What**: A thin, testable wrapper around “things the agent can do”.
- **Where (code)**: `src/colossus_blender/viga/skills.py`
- **Examples**:
  - generate a plan
  - execute code in Blender
  - initialize camera viewpoint for diagnostics
  - adjust camera based on an instruction

### 6) Model Adapters (VLM Providers)
- **What**: A small abstraction over different model backends.
- **Where (code)**: `src/colossus_blender/viga/modern_models.py`
- **Supported**:
  - Qwen3-VL via OpenAI-compatible `/v1/chat/completions`
  - Gemini 3 via Google AI Studio API (`:generateContent`)

### 7) Shared Vision Utilities
- **What**: Helpers for normalizing endpoints and extracting structured blocks from LLM responses.
- **Where (code)**: `src/colossus_blender/vision_utils.py`
- **Critical behavior**: robust extraction of code blocks returned by models.

## How Data Flows

A single iteration typically follows:
- task + memory → Generator (plan + code)
- code → MCP → Blender scene update
- scene/renders → Verifier → feedback
- feedback → memory → next iteration

For the detailed step-by-step pipeline, see docs/pipeline.md.

## Documentation Map

- Pipeline overview: docs/pipeline_overview.md
- Pipeline deep dive: docs/pipeline.md
- Model backends: docs/models/models.md
- Prompts: docs/prompts/prompts.md
- MCP bridge: docs/mcp/mcp.md
- VIGA internals: docs/viga/viga.md
- Skills/tooling: docs/skills/skills.md
- Dev docs: docs/dev/dev.md
- Plans (stacked PR strategy): docs/plans/plans.md
