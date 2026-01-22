# Attempt Coordinator Plan

This plan defines the next architectural step: treat a VIGA run as one **attempt**, and introduce an **outer Attempt Coordinator** that runs multiple attempts from the same initial conditions, selects the best outcome, and optionally performs self-looping retries.

## Why: attempts, not one-shot

A single VIGA refinement loop (Generator → Execute → Verify → Memory) is necessary but not sufficient for production-grade asset generation.

We need:
- **Multiple independent attempts** from the same baseline to escape local minima.
- A **selection mechanism** to pick the best attempt.
- A **self-loop** to re-run an attempt when failure is due to transient conditions (timeouts, parse issues, Blender hiccups).
- A path to **parallel attempts**.

## Definitions

- **Attempt**: a fresh run starting from the same baseline scene and/or same reference inputs.
- **Iteration**: one inner VIGA loop step.
- **Baseline**: the initial state that each attempt starts from.
- **Artifacts**: persisted outputs from attempts/iterations (plans, code, renders, scores).

## Aspect 1 — Baseline reset and replayability

Goal: every attempt starts from a *known* state.

Deliverables:
- A clear baseline strategy (see docs/plans/blender_reset_and_baselines.md).
- A repeatable “reset” operation before each attempt.

Requirements:
- Deterministic scene reset.
- Isolation between attempts (no leaked objects/materials).
- Consistent camera/lighting for diagnostics.

## Aspect 2 — Outer attempt loop design

Goal: orchestrate N attempts and select the best.

Proposed interface (conceptual):
- `AttemptCoordinator.run(task, baseline, attempts=N, iterations=K) -> BestAttemptResult`

Responsibilities:
- Prepare baseline for attempt `i`.
- Run inner VIGA loop.
- Collect artifacts.
- Score attempt.
- Select best.

Stop conditions:
- Best score exceeds threshold.
- Attempts exhausted.
- Operator stop.

## Aspect 3 — Scoring and selection

Goal: choose the best attempt reliably.

We need:
- A structured verifier output format.
- A score function that is stable across camera/render noise.

See docs/plans/scoring_and_selection.md.

## Aspect 4 — Failure taxonomy (enables self-loop)

Goal: don’t waste iterations on trivial failures.

Classify failures into:
- **E0: Infrastructure** (MCP connection, Blender not ready)
- **E1: Execution** (Blender Python exception)
- **E2: Output format** (model didn’t return code fence)
- **E3: Semantic** (visual mismatch; normal VIGA feedback)

Policy:
- E0/E1/E2 → immediate self-fix/self-loop path before spending full visual verification.
- E3 → normal refinement iterations.

## Aspect 5 — Artifact schema & reproducibility

Goal: make every attempt reviewable and replayable.

- Define run folder structure and JSON schemas.
- Standardize naming, timestamps, and seed IDs.

See docs/plans/artifacts_and_reproducibility.md.

## Aspect 6 — Parallelization strategy

Goal: scale attempts without destabilizing Blender.

- Prefer “one Blender per worker” over multiplexing a single Blender.
- Introduce a worker pool model.

See docs/plans/parallelization_workers.md.

## Aspect 7 — Tests and validation

Goal: ensure attempt coordination is correct without requiring Blender.

- Unit tests for coordinator logic with mocked VIGA loop.
- Contract tests for artifact schema.
- Optional E2E tests gated behind an environment flag (requires Blender).

## Aspect 8 — Integration with upstream repo + monorepo path

Goal: we will eventually combine repos (pipeline up to rough hull + this repo).

We should design attempt orchestration and artifact schema so they can be shared.

- Upstream integration: docs/plans/integration_with_upstream_repo.md
- Monorepo migration: docs/plans/monorepo_migration.md

## Implementation stages (stack-friendly)

Stage A — Plan + schemas (docs-only)
- Write/approve these plan documents.
- Decide baseline strategy.
- Decide scoring format.

Stage B — Minimal AttemptCoordinator (no parallelism)
- Implement coordinator that runs attempts sequentially.
- Implement reset hook (even if stubbed behind an interface).
- Persist artifacts.

Stage C — Scoring + selection
- Structured verifier output.
- Deterministic diagnostic render pack.
- Best-attempt selection.

Stage D — Self-loop policies
- Failure taxonomy.
- Fast retry behavior.

Stage E — Worker pool (parallel)
- N workers, each with its own Blender.
- Attempt queue.

Stage F — Monorepo readiness
- Move shared interfaces into a common package.
- Harmonize configuration and docs.
