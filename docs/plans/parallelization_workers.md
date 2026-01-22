# Parallelization and Workers

This document defines how to parallelize attempts safely.

## Constraints

- Blender is stateful.
- Generated code is not guaranteed to be isolated.
- MCP connections are per Blender instance.

## Recommended model: worker pool

- Run **N worker processes**, each with:
  - its own Blender instance,
  - its own MCP port,
  - its own working directory.

- The Attempt Coordinator dispatches attempt jobs to workers.

## Why “one Blender per worker”

Pros:
- Strong isolation.
- Easy crash containment.
- Deterministic baseline loading.

Cons:
- More RAM/VRAM usage.
- Need port management.

## Scheduling options

### Option A — Local multi-process
- N Blender instances on one machine.
- Suitable for 1–4 parallel attempts on a workstation.

### Option B — Remote workers
- Multiple machines running Blender headless.
- Coordinator dispatches jobs over RPC.

This connects naturally to the existing remote infrastructure notes.

## Artifact collisions

Each worker must write to a unique run folder.

## Testing strategy

- Unit test the scheduler with fake workers.
- Integration test with 1 real worker, gated behind a flag.
