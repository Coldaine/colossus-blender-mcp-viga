# Blender Reset and Baselines

This document defines how we guarantee that each **attempt** starts from the same initial conditions.

## Core requirement

If attempts start from different states, the outer loop becomes unreproducible and selection becomes noisy.

We want:
- deterministic reset,
- low overhead,
- minimal “state leakage” between attempts.

## Baseline strategies

### Strategy A — Load a baseline `.blend` each attempt (recommended)

Approach:
- Keep a baseline file under a known location (e.g., `assets/baselines/<name>.blend`).
- At attempt start, instruct Blender to open that file.

Pros:
- Most deterministic.
- Captures camera, lighting, render settings, collections, everything.

Cons:
- Requires a Blender-side operation to open files.
- Must ensure the MCP addon remains available after opening.

### Strategy B — Reset scene via Python (fast, but fragile)

Approach:
- Delete all non-default objects/collections.
- Purge orphan data blocks.
- Restore render settings/camera.

Pros:
- No file I/O.

Cons:
- Easy to miss state (materials, node groups, world settings).
- Harder to keep fully deterministic.

### Strategy C — Namespacing + cleanup (for multi-attempt in one scene)

Approach:
- Each attempt writes everything into a dedicated collection.
- Reset = delete that collection.

Pros:
- Enables fast repeated attempts without reloading.

Cons:
- Still leaks if anything is written outside the attempt namespace.
- Harder to guarantee with arbitrary generated code.

## Recommendation

Start with Strategy A.
- It is the most reliable base for scoring and parallelization.
- It also fits the “one Blender per worker” model.

## Reset interface (design)

Introduce a skill:
- `reset_to_baseline(baseline_id: str) -> ResetResult`

Where baseline_id maps to:
- a `.blend` file path, and
- an optional reference image bundle (if used).

## Reference images and initial inputs

If you want to run attempts from the same “start image”, clarify:
- Is the image purely a target reference (verifier input)?
- Or does it represent a reconstructed initial scene?

For now:
- Treat the image as a **target reference** consumed by the verifier.
- The baseline `.blend` controls the starting geometry/camera.

## What to standardize for scoring

To compare attempts fairly, fix:
- diagnostic camera pack (same poses),
- diagnostic lighting (optional override),
- render resolution and downscale,
- render output format.

## .obj fixtures

When you provide example `.obj` files, use them as:
- import sanity checks,
- baseline creation inputs,
- regression fixtures for “reset works” (scene returns to known state).

These fixtures also support automated tests that validate:
- import succeeded,
- scene bounding box matches expectation,
- camera framing remains stable.
