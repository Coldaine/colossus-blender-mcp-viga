# Master Transition Plan (Docs → Implementation)

This document is the *single* high-level execution order for turning the existing planning set into a working system.

It does two things:
1) references the existing plan documents in the order we should execute them, and
2) defines the **codebase structure we are transitioning toward** as we implement those plans.

## Guiding principle

- Documentation can be split into subdomains for clarity.
- Code should follow the **minimal structure demanded by the runtime system**, and only modularize when it reduces coupling or improves testability.

In practice: prefer a small number of stable, well-defined boundaries:
- **Blender bridge (MCP runtime)**
- **Agent loop (VIGA)**
- **Vision evaluation (VLM + parsing)**
- **Artifacts (persistence + replay)**
- **Attempt orchestration (outer loop)**

## Current reality check (why this plan exists)

Right now, we have:
- A working *conceptual* architecture (see [../architecture.md](../architecture.md) and [../pipeline_overview.md](../pipeline_overview.md)).
- A set of detailed “outer-loop” plans (see [plans.md](plans.md)).
- A Blender-side addon ([../../config/addon.py](../../config/addon.py)) whose message protocol and tool surface should be treated as the source of truth.

The highest-risk drift is implementing coordinator/scoring/parallelism **before** the MCP bridge contract and verifier output format are stable.

## Target code structure (end state)

This is the structure we should converge to. It prioritizes **shared state** for multi-agent coordination.

```
src/colossus_blender/
  __init__.py

  # 1. THE SHARED STATE (The "Brain")
  state_manager/
    context.py             # The "Truth": current plan, history, artifact paths
    persistence.py         # Saves the state to disk (run.json, attempt.json)

  # 2. THE INFRASTRUCTURE (The "Hands")
  runtime/
    mcp_client.py          # Standard MCP client (GenesisCore/Std compatible)
    rendering.py           # Helper for standardizing diagnostic views
    baselines.py           # Logic to load initial .blend states

  # 3. THE AGENTS (The "Workers")
  agents/
    coordinator.py         # BROAD SEARCH: Manages N attempts & workers
    planner.py             # Decomposes the user request
    designer.py            # Generates initial geometry
    refiner.py             # VIGA Loop: Analysis-by-Synthesis patches

  # 4. THE SENSES (The "Eyes")
  vision/
    evaluator.py           # VLM calling & structured scoring
    parsing.py             # Extracting JSON/Code from model outputs

  # 5. LEGACY / EXPERIMENTAL
  experiments/
    ...
```

## Execution order (phased)

### Phase 0 — Infrastructure alignment (Standard Server)

**Goal:** Stop maintaining custom addon code; rely on standard MCP tools.

Deliverables:
- **Deprecate local `config/addon.py`.**
- Update `runtime/mcp_client.py` to consume standard tools (e.g., `create_object` or `run_script` from standard servers).
- Verify basic operations (Reset, Render, Execute) work against the chosen Standard Server.

### Phase 1 — The Broad Loop (Attempt Coordinator)

**Goal:** Run N parallel attempts early, even if they are simple.

Deliverables:
- Implement `agents/coordinator.py`.
- Implement `state_manager` to track the lifecycle of N attempts.
- Ensure we can spin up 3 attempts and save their logs to unique folders.

### Phase 2 — The Multi-Agent Inner Loop (Designer + Refiner)

**Goal:** Stateful progression, not just "re-running scripts".

Deliverables:
- Split the monolithic VIGA loop into:
  - **Designer:** Creates the base state (from baseline or script).
  - **Refiner:** Applies patch-based corrections driven by vision.
- Connect them via `state_manager`.

### Phase 3 — Vision & Scoring

**Goal:** Automate the "winner selection" for the Broad Search.

Deliverables:
- Wired `vision/evaluator.py` to the Coordinator.
- Coordinator uses the score to sort attempts (best of N).

### Phase 4 — Artifact & Reproducibility Polish

**Goal:** Deep inspection.

Deliverables:
- Full serialization of the `state_manager` at every step.
- Replay scripts.

## What we are *not* doing yet

- We are not refactoring code purely to match documentation subdomains.
- We are not implementing parallelism before the bridge contract and artifacts are solid.
- We are not moving to a monorepo until the handoff contract is proven.

## Success criteria

A “transition complete” milestone means:
- One-click (or one CLI command) run produces a `runs/...` folder with attempt artifacts.
- Attempts are comparable via deterministic renders + structured verifier output.
- The selected best attempt is reproducible from baseline.
