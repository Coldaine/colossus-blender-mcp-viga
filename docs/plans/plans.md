# Plans

This subdomain contains project plans that are larger than a single issue.

## Attempt Coordinator Roadmap

These documents define the next evolution: multiple attempts from the same baseline, selection, self-looping, and eventual parallelization.

- [attempt_coordinator.md](attempt_coordinator.md) — Two-level controller design
- [blender_reset_and_baselines.md](blender_reset_and_baselines.md) — Deterministic scene reset
- [scoring_and_selection.md](scoring_and_selection.md) — Scoring attempts, selecting best
- [self_correction_loop.md](self_correction_loop.md) — Fast retry for code errors
- [artifacts_and_reproducibility.md](artifacts_and_reproducibility.md) — Run artifacts schema
- [parallelization_workers.md](parallelization_workers.md) — Worker pool for parallel attempts
- [integration_with_upstream_repo.md](integration_with_upstream_repo.md) — Rough hull handoff
- [monorepo_migration.md](monorepo_migration.md) — Unifying repositories

## Stacked PR (Staged) Delivery Plan

We want changes to land as small, reviewable steps via stacked pull requests, rather than one massive PR.

### Principles

- Each PR should be reviewable in isolation.
- Each PR should keep the repository runnable (or clearly state what is broken and why).
- Prefer doc-only PRs first when doing major documentation refactors.

### Proposed PR Stack (Docs + Pipeline)

1) **PR 1: Documentation schema + index**
   - Add/confirm [../requirements.md](../requirements.md), [../CHANGELOG.md](../CHANGELOG.md), [../todo.md](../todo.md)
   - Establish the subdomain folder pattern and the master-doc naming rule

2) **PR 2: Architecture + pipeline docs**
   - Add [../architecture.md](../architecture.md)
   - Add [../pipeline_overview.md](../pipeline_overview.md) and [../pipeline.md](../pipeline.md)
   - Update root README to point to docs/

3) **PR 3: Subdomain docs**
   - Add [../models/models.md](../models/models.md), [../mcp/mcp.md](../mcp/mcp.md), [../viga/viga.md](../viga/viga.md), [../skills/skills.md](../skills/skills.md)
   - Add [../dev/testing.md](../dev/testing.md) and [../dev/logging.md](../dev/logging.md)

4) **PR 4: Consolidate legacy docs**
   - Move legacy docs into subfolders (or convert to redirects)
   - Remove stale references (especially deprecated a/docs)

### If changes already landed

If some or all of the above has already been merged, treat the plan as:
- a checklist to verify we didn’t miss anything, and
- guidance for how we stage the *next* wave of work (new skills, new models, end-to-end runs).

### How to manage the stack (workflow)

- Create a base branch (e.g. `docs/schema`).
- Open PR 1.
- Branch PR 2 off PR 1 (e.g. `docs/pipeline`), open PR 2 targeting PR 1.
- Continue stacking.
- Merge from bottom to top once each PR is approved.

## Related docs

- Existing staging notes: [pr_staging.md](pr_staging.md)
- Remote infrastructure: [remote_infrastructure.md](remote_infrastructure.md)
