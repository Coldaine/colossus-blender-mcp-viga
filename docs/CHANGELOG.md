# Changelog

All notable changes to documentation and the VIGA pipeline should be recorded here.

## Unreleased

### Added
- `docs/archive/`, `src/archive/`, `tests/archive/` to preserve legacy work without polluting the active rebuild.
- Archive READMEs and updated docs navigation to reflect the rebuild.

### Changed
- Repository repositioned as a personal tooling + exploration repo undergoing a clean rebuild.
- Documentation workflow updated to use `MASTER_REQUIREMENTS.md` + `docs/plans/*` as the source of truth.

### Fixed
- Removed stale references in docs index and assistant instructions after archiving legacy pipeline/VIGA documentation.

### Added
- Documentation schema and subdomain layout.
- **Attempt Coordinator plan** with 8 detailed design documents:
  - `attempt_coordinator.md`: Two-level controller (outer attempt loop).
  - `blender_reset_and_baselines.md`: Deterministic scene reset strategies.
  - `scoring_and_selection.md`: Structured verifier output and selection logic.
  - `self_correction_loop.md`: Fast retry for execution/format errors.
  - `artifacts_and_reproducibility.md`: Run folder structure and schemas.
  - `parallelization_workers.md`: Worker pool for parallel attempts.
  - `integration_with_upstream_repo.md`: Rough hull pipeline handoff.
  - `monorepo_migration.md`: Path to unified repository.

### Changed
- Reorganized docs into subdomain folders.

### Fixed
- Removed deprecated `a/docs` references.

## 0.4.0 (Jan 2026)

- Baseline VIGA documentation and initial implementation notes.
