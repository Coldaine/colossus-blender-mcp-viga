# Integration with Upstream Repo (Rough Hull Pipeline)

You described a second repository that handles the pipeline “up until we have the crafted rough hull”.
This document plans for integrating that upstream pipeline with this repo.

## Integration philosophy

- Keep coupling low.
- Prefer artifact contracts over direct code imports.

## Proposed handshake

Upstream outputs:
- baseline `.blend` (or `.obj` + scene recipe)
- a “rough hull” collection already placed
- reference images (target and/or intermediate renders)
- metadata (scale, units, coordinate conventions)

This repo consumes:
- baseline_id + artifact path
- target spec and references

This repo outputs:
- refined attempts (scene edits)
- best selected attempt
- export artifacts (glb/fbx/obj)

## What must be standardized

- Units and scale conventions.
- Coordinate frame conventions (Blender axes).
- Object naming conventions (for heuristics and verification).

## Near-term plan (before monorepo)

- Define the run artifact structure (docs/plans/artifacts_and_reproducibility.md).
- Add a CLI entry that takes a baseline path and task.
- Create one integration test that loads an upstream-produced baseline.

## Monorepo note

Once you decide to unify repos, the artifact contract can remain the boundary inside the monorepo, keeping components independently testable.
