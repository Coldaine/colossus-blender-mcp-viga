# Prompts

This subdomain documents the prompts used by the system.

## Where prompts live

- The repository prompt templates currently live under `prompts/`.
- The VIGA agents also embed some prompts inline (planning, camera translation).

## Prompt categories

### 1) System prompts
- Define role, constraints, and output format.
- Example: a “Blender Python expert” system instruction that demands code-only output.

### 2) Planning prompts
- Inputs: task spec + memory context.
- Output: next-iteration plan.

### 3) Code synthesis prompts
- Inputs: plan + task + memory context.
- Output: a single Python fenced code block.

### 4) Verification prompts
- Inputs: renders + acceptance criteria.
- Output: actionable feedback.

## Output format requirements

- **Code must be fenced** so `extract_code_from_response()` can reliably parse it.
- If you need structured outputs (JSON), fence them as ` ```json ... ``` `.

## Related docs

- Code extraction behavior: `src/colossus_blender/vision_utils.py`
- Model adapters: docs/models/models.md
