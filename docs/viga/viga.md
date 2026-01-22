# VIGA

This subdomain documents the VIGA (Vision-as-Inverse-Graphics) architecture as implemented in this repo.

## What VIGA means here

VIGA treats 3D modeling as an iterative search:
- propose edits (code)
- apply edits (execute in Blender)
- observe results (renders/scene info)
- critique and refine (verifier feedback)

## Code map

- Loop + agents: `src/colossus_blender/viga/agent.py`
- Memory: `src/colossus_blender/viga/memory.py`
- Skills/tool surface: `src/colossus_blender/viga/skills.py`
- Model adapters: `src/colossus_blender/viga/modern_models.py`

## Iteration memory

- The memory keeps the last *L* iterations (Tail_L).
- Each iteration records: plan, code, feedback.

## Generator vs Verifier

- **Generator**: produces the next plan + code increment.
- **Verifier**: positions the camera, requests diagnostics, and returns actionable critique.

## Related docs

- Legacy deep dives:
  - [agent_design.md](agent_design.md)
  - [viga_algorithm.md](viga_algorithm.md)
