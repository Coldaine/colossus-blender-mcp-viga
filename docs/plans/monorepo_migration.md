# Monorepo Migration Plan

This document outlines how to migrate toward a monorepo, if/when you choose to unify the upstream pipeline with this repo.

## When to start a monorepo

Start immediately if:
- you need shared interfaces (artifacts schema, baseline manager, worker pool) right now,
- you expect frequent cross-repo changes.

Delay if:
- you want to stabilize the Attempt Coordinator first,
- upstream repo is still churning and you don’t want churn to destabilize this repo.

## Recommended approach: staged monorepo

### Stage 1 — Shared contract package
- Create a shared Python package (e.g., `colossus_contracts`) containing:
  - artifact schemas
  - baseline identifiers
  - common config parsing

### Stage 2 — Monorepo structure

Example:

```
repo/
  packages/
    contracts/
    blender_mcp/
    rough_hull_pipeline/
    viga_refinement/
  docs/
  scripts/
```

### Stage 3 — Consolidate CI and docs

- Single docs index.
- Separate subdomain docs per package.

## Risks

- Large moves can break import paths.
- Git history becomes harder to track if done in one big change.

## Mitigation

- Keep artifact contract stable.
- Use stacked PRs for any big move.
- Add a compatibility layer for old import paths temporarily.
