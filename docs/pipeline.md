# Pipeline (Deep Dive)

This document is the definitive, step-by-step description of what happens during a VIGA run.

## Terminology

- **Iteration**: One Generator→Execute→Verifier cycle.
- **Plan**: Natural-language steps describing the next edit.
- **Code**: Blender Python executed in Blender.
- **Feedback**: The verifier’s critique and next corrective suggestions.

## Step-by-step

### 0) Startup and configuration
- Configure model backend (Qwen3-VL endpoint or Gemini API key).
- Ensure Blender is running with the MCP addon and is reachable.

### 1) Build context window
- The memory selects the last *L* iterations (Tail_L) and formats them into a compact context block.
- Purpose: provide continuity without growing unbounded.

### 2) Generator: plan
- The generator prompts the model to produce a plan grounded in the task + memory context.
- Output: plan text (may include structured content).

### 3) Generator: code synthesis
- The generator prompts the model to output **only Blender Python**.
- The system extracts the first fenced code block (```python … ```).
- Output: executable code string.

Failure modes:
- Model outputs prose instead of code → extraction returns empty → iteration fails fast.
- Model outputs multiple blocks → first block wins by design.

### 4) Execute: MCP → Blender
- The code is transmitted to Blender and executed.
- Output: execution result (stdout/stderr and any structured return value supported by MCP).

Failure modes:
- Connection issues → MCP errors.
- Blender exceptions → surfaced to the outer loop; typically stored as feedback.

### 5) Verifier: normalize viewpoint
- The verifier calls the viewpoint initializer.
- It computes a combined bounding box over mesh objects, then positions the camera to frame the scene with padding.

### 6) Verifier: investigation (optional)
- If the verifier needs a different angle, it can issue a natural-language camera adjustment.
- A fast-path handles common phrases; otherwise an LLM translates the instruction into Blender camera code.

### 7) Verifier: render and critique
- The verifier obtains renders/diagnostic images from Blender.
- Those images + a verification prompt are sent to the VLM.
- Output: feedback string describing mismatches and suggested corrections.

### 8) Persist to memory
- Store:
  - the plan
  - the executed code
  - the verification feedback
  - (optionally) execution metadata or image IDs

### 9) Stop conditions
Typical stop conditions:
- Max iterations reached.
- Verifier reports acceptance criteria met.
- Human operator stops the run.

## What is “correct” output?

- Code must be fenced or otherwise parseable into a Python snippet.
- Code should be **incremental**: small changes each iteration reduce failure risk.
- Verifier feedback should be actionable: concrete geometry/camera/material issues.

## Where to look in code

- Main loop: `src/colossus_blender/viga/agent.py`
- Memory: `src/colossus_blender/viga/memory.py`
- Skills: `src/colossus_blender/viga/skills.py`
- Models: `src/colossus_blender/viga/modern_models.py`
- Utilities: `src/colossus_blender/vision_utils.py`
