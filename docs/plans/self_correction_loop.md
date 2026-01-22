# Self-Correction Loop (Fast Retry)

This document defines how to handle **trivial failures** without wasting a full VIGA iteration.

## Problem

Currently, every failure goes through the full visual verification cycle:
1. Generator produces code.
2. Code is executed.
3. Verifier runs, inspects scene, returns feedback.
4. Memory stores iteration.

But some failures are **trivial**:
- Blender Python exception (syntax error, API misuse).
- Model returned prose instead of fenced code.
- MCP connection hiccup.

Spending a full visual cycle on these wastes time and pollutes memory with non-semantic feedback.

## Solution: Fast Inner Retry

Before invoking the Verifier, check if execution succeeded. If not, give the Generator a chance to fix its own code.

```
┌─────────────────────────────────────────────────────────────┐
│                       VIGA Iteration                        │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │ Generator│───▶│ Execute  │───▶│ Verifier │               │
│  └──────────┘    └────┬─────┘    └──────────┘               │
│                       │                                      │
│                       ▼                                      │
│                  ┌─────────┐                                │
│                  │ Failed? │                                │
│                  └────┬────┘                                │
│                       │ yes                                  │
│                       ▼                                      │
│              ┌────────────────┐                             │
│              │ Fast Retry Loop│ (up to 3 attempts)          │
│              │ - show error   │                             │
│              │ - ask for fix  │                             │
│              │ - re-execute   │                             │
│              └────────────────┘                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Failure Classification

| Class | Examples | Action |
|-------|----------|--------|
| **E0: Infrastructure** | MCP not connected, Blender crashed | Abort attempt, restart worker |
| **E1: Execution** | Blender exception, invalid API call | Fast retry with error message |
| **E2: Format** | No code fence, malformed output | Fast retry with format reminder |
| **E3: Semantic** | Code ran, but result is wrong | Normal verification cycle |

Only E1 and E2 enter the fast retry loop. E0 escalates. E3 proceeds normally.

## Fast Retry Prompt

When entering fast retry:

```
Your previous code failed to execute.

Error:
{error_message}

Please fix the code. Return ONLY the corrected Python code in a fenced block.
Do not explain, just provide the fixed code.
```

## Retry Limits

- Max fast retries per iteration: 3
- If all fail, record as E1/E2 failure and proceed to Verifier (which will likely score low).

## Impact on Memory

Fast retries are **not** stored as separate iterations. Instead:
- Store the final successful code (or last failed attempt).
- Store a `retry_count` field.
- Optionally store error summaries for debugging.

This keeps memory focused on semantic progression, not syntax fumbling.

## Implementation

Modify `GeneratorAgent.generate_step()`:

```python
async def generate_step(self, task: str, context: str) -> IterationContext:
    # ... plan and code generation ...
    
    code = self.extract_code(response)
    
    for retry in range(self.max_retries):
        result = await self.skills.execute_code(code)
        
        if result.success:
            break
        
        if retry < self.max_retries - 1:
            code = await self.fast_fix(code, result.error)
    
    return IterationContext(
        plan=plan,
        code=code,
        execution_result=result,
        retry_count=retry,
    )

async def fast_fix(self, code: str, error: str) -> str:
    prompt = f"""Your code failed with this error:
{error}

Fix the code. Return ONLY the corrected Python in a fenced block."""
    
    response = await self.model.generate_text(
        "You are a Blender Python expert. Output only valid code.",
        prompt
    )
    return self.extract_code(response)
```

## Testing

Add tests for:
- `test_fast_retry_fixes_syntax_error`
- `test_fast_retry_gives_up_after_max`
- `test_fast_retry_does_not_trigger_on_success`
- `test_fast_retry_count_is_recorded`

## Implementation Checklist

- [ ] Add `fast_fix()` method to GeneratorAgent.
- [ ] Modify `generate_step()` to include retry loop.
- [ ] Add `retry_count` to `IterationContext`.
- [ ] Add failure classification logic.
- [ ] Add tests.
- [ ] Update docs/pipeline.md with retry behavior.
