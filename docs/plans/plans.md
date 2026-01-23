# Plans

This subdomain contains project plans that are larger than a single issue.

## Phase Plans (Start Here)

These are the executable implementation plans:

- [phase_1_mvp_inner_loop.md](phase_1_mvp_inner_loop.md) — **Phase I: MVP inner loop** (single attempt, Builder + Evaluator)
- [phase_2_broad_search.md](phase_2_broad_search.md) — **Phase II: Broad search** (N parallel attempts, selection)

## Master Requirements

- [../MASTER_REQUIREMENTS.md](../MASTER_REQUIREMENTS.md) — Exhaustive requirements document with architecture, state schemas, and tool specs

## Master Transition Plan (Reference)

- [transition_master_plan.md](transition_master_plan.md) — High-level execution order + target code structure

## Attempt Coordinator Roadmap (Reference)

These documents define the next evolution: multiple attempts from the same baseline, selection, self-looping, and eventual parallelization.

- [attempt_coordinator.md](attempt_coordinator.md) — Two-level controller design
- [blender_reset_and_baselines.md](blender_reset_and_baselines.md) — Deterministic scene reset
- [scoring_and_selection.md](scoring_and_selection.md) — Scoring attempts, selecting best
- [self_correction_loop.md](self_correction_loop.md) — Fast retry for code errors
- [artifacts_and_reproducibility.md](artifacts_and_reproducibility.md) — Run artifacts schema
- [parallelization_workers.md](parallelization_workers.md) — Worker pool for parallel attempts
- [integration_with_upstream_repo.md](integration_with_upstream_repo.md) — Rough hull handoff
- [monorepo_migration.md](monorepo_migration.md) — Unifying repositories

## Related docs

- Remote infrastructure: [remote_infrastructure.md](remote_infrastructure.md)
- Archive index: [../archive/README.md](../archive/README.md)
