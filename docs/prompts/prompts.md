# Prompts

This subdomain documents the prompts used by the system.

## Where prompts live

- The repository prompt templates currently live under `prompts/`.
- Legacy code embedded additional prompts inline; those implementations are now archived under `src/archive/`.

## TODO (keep updated)

- Treat `prompts/` as an evolving library: periodically prune, rewrite, and re-align prompts with the current Phase I/II architecture.

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

- Code extraction behavior: (rebuild in progress; legacy utilities are archived under `src/archive/`)
- Model adapters: docs/models/models.md
