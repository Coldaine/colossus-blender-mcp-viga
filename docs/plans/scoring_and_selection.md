# Scoring and Selection

This document defines how the Attempt Coordinator scores attempts and selects the “best” result.

## Why scoring matters

Attempts are only useful if we can:
- compare outcomes reliably,
- pick the best without manual inspection (or at least reduce manual effort).

## Scoring surfaces

### Surface 1 — Verifier score (primary)

The Verifier should output a structured object:
- `score`: float in [0, 1]
- `critical_issues`: list
- `noncritical_issues`: list
- `recommended_next_actions`: list
- `pass`: boolean (optional)

This can be JSON fenced output from the model.

### Surface 2 — Execution health (secondary)

Penalize attempts with:
- Blender exceptions,
- repeated retries,
- MCP timeouts,
- missing render artifacts.

### Surface 3 — Heuristic metrics (optional)

Without deep geometry comparison, we can still track:
- object count and types,
- bounding box dimensions,
- triangle/poly count (if accessible),
- presence of required named objects.

## Stability: reduce camera noise

Attempt comparison becomes unstable if each attempt renders from a different view.

We should standardize:
- a canonical camera pose set (front/side/top/isometric),
- consistent framing and downscale,
- consistent lighting for diagnostics.

## Selection strategies

### Strategy A — Best final score
Pick attempt with max final verifier score.

### Strategy B — Best trajectory
Pick attempt with best improvement trajectory:
- large score delta from early iterations,
- fewer regressions.

### Strategy C — Pareto selection (future)
Select a set of top candidates to seed further attempts.

## Seeded self-loop

Once a “best” attempt is selected, we can run a self-loop:
- reset baseline
- run another attempt with a **different strategy prompt** based on the best attempt’s failure modes

Examples:
- “focus on proportions first”
- “avoid boolean operations until late”

This requires storing structured feedback.

## Testing

We can test scoring without Blender by:
- mocking verifier outputs with known scores,
- ensuring selection logic is deterministic.
