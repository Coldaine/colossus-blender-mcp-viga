# Pipeline Overview

This is the “what happens” overview of the runtime pipeline. It is intentionally more operational than docs/architecture.md.

## Inputs

- A **task specification** (e.g., “model a WWII battleship hull with correct proportions”).
- A running **Blender + MCP** instance connected to the agent.
- A configured **vision-language model** (Qwen3-VL locally, or Gemini via API).

## The Closed Loop (High-Level)

1) **Context build**
- The agent builds a compact context string from recent iterations (plan/code/feedback).

2) **Plan**
- The Generator produces a short plan for the next iteration.

3) **Synthesize edits**
- The Generator emits Blender Python code that implements the next increment.

4) **Execute in Blender**
- Code is sent over MCP and executed inside Blender.

5) **Normalize viewpoint**
- The Verifier positions the camera to a stable, diagnostic viewpoint that frames the scene.

6) **Verify**
- The Verifier requests renders (or other visual diagnostics) and asks the VLM to critique against the target spec.

7) **Persist iteration**
- Plan/code/feedback are appended to the sliding memory window.

8) **Repeat**
- Continue until a stop condition is reached (quality threshold, max iterations, or explicit “done”).

## Outputs

- Updated Blender scene.
- Iteration memory containing what was tried and what the verifier observed.

For the precise messages, artifacts, and failure modes, see docs/pipeline.md.
