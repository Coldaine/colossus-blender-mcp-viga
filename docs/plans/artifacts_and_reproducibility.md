# Artifacts and Reproducibility

This document defines the output artifacts we persist for attempts and iterations.

## Goals

- Make every attempt inspectable.
- Make every attempt replayable.
- Enable downstream tooling (dashboards, comparisons, dataset creation).

## Proposed run folder structure

Create a run directory, e.g.:

```
runs/
  2026-01-22T15-40-11Z_task-<slug>_baseline-<id>/
    run.json
    attempts/
      attempt-000/
        attempt.json
        iterations/
          iter-000.json
          iter-000_code.py
          renders/
            front.png
            side.png
            top.png
            iso.png
          verifier.json
          generator_plan.txt
          generator_raw.txt
          verifier_raw.txt
      attempt-001/
        ...
```

## Core schemas

### run.json
- task
- baseline_id
- model identifiers
- coordinator configuration
- start/end timestamps

### attempt.json
- attempt_id
- seed / strategy label
- final score
- summary of failure modes

### iter-XXX.json
- iteration number
- plan
- extracted code
- execution result
- render file names
- verifier structured output

## Determinism knobs

- baseline reset strategy
- fixed diagnostic camera pack
- fixed render settings for diagnostics

## Privacy and secrets

Never persist:
- API keys
- tokens

If prompts include secrets, store redacted summaries.

## Why this matters for future monorepo

When combining with your upstream “rough hull” repo, artifacts become the handshake:
- upstream produces baseline + rough hull artifacts
- this repo consumes them and produces refined attempts

A shared artifacts contract reduces coupling.
