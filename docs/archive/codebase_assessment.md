# Codebase Assessment: Greenfield vs Reuse

**Date:** January 2026  
**Purpose:** Evaluate existing code for reuse in Phase I/II implementation

**Cross-references:**
- [phase_1_mvp_inner_loop.md](./phase_1_mvp_inner_loop.md)
- [phase_2_broad_search.md](./phase_2_broad_search.md)
- [MASTER_REQUIREMENTS.md](../MASTER_REQUIREMENTS.md)

---

## 1. Executive Summary

**Recommendation: Hybrid approach — keep useful components, rewrite orchestration.**

| Category | Verdict | Rationale |
|----------|---------|-----------|
| MCP Client | ✅ **Keep** | Working socket-based client, just needs new tools |
| Blender Addon | ✅ **Keep** | Working server, add new tool handlers |
| Model Adapters | ✅ **Keep** | Qwen3VL, Gemini3Pro work; add role-based routing |
| Vision Utilities | ✅ **Keep** | Code extraction, JSON parsing, image utils |
| VIGA Memory | ⚠️ **Replace** | Too simple for LangGraph state; use new schema |
| VIGA Agent | ⚠️ **Replace** | Doesn't fit LangGraph node pattern |
| Orchestrator | ❌ **Delete** | Legacy D5 pattern, fully superseded |
| Game Asset Agent | ✅ **Keep** | Standalone, use as finalization stage |
| GPU Config | ✅ **Keep** | Useful for render presets |
| GLM Vision | ✅ **Keep** | Optional alternative verifier |

---

## 2. Detailed Assessment

### 2.1 `mcp_client.py` — ✅ KEEP

**What it does:**
- Socket-based connection to Blender addon
- `execute_code()`, `get_scene_info()`, `get_viewport_screenshot()`, `clear_scene()`
- Async interface

**What's good:**
- Clean async design
- Working socket protocol
- Good error handling

**What needs change:**
- Add `reset_to_baseline(path)` method
- Add `export_blend(path)` method
- Add `set_camera_pose(location, rotation)` method
- Add `get_diagnostic_renders()` method (multi-view pack)
- Consider abstracting to support future MCP protocol if needed

**Effort:** Low (add 4-5 new methods)

---

### 2.2 `config/addon.py` — ✅ KEEP

**What it does:**
- Blender-side MCP server (socket listener)
- Command handlers for `execute_code`, `get_scene_info`, `get_viewport_screenshot`
- PolyHaven, Sketchfab, Rodin integrations

**What's good:**
- Production-quality socket server
- Robust command dispatch
- Image encoding works

**What needs change:**
- Add handler for `reset_to_baseline`
- Add handler for `export_blend`
- Add handler for `set_camera_pose`
- Add handler for `get_diagnostic_renders` (front/side/top/iso)
- Consider removing unused integrations (Rodin, etc.) to simplify

**Effort:** Low-Medium (add 4 handlers, ~100 lines each)

---

### 2.3 `viga/modern_models.py` — ✅ KEEP

**What it does:**
- `FoundationModel` ABC with `generate_text(system, user, images)`
- `Qwen3VL` implementation (local OpenAI-compatible endpoint)
- `Gemini3Pro` implementation (Google AI Studio API)
- `MockModel` for testing

**What's good:**
- Clean abstraction
- Image support
- Fallback on multimodal rejection
- Configurable via env vars

**What needs change:**
- Add model health check method
- Add role-based factory (get model for "builder" vs "evaluator")
- Log which model was used per call

**Effort:** Low (add 2-3 methods)

---

### 2.4 `vision_utils.py` — ✅ KEEP

**What it does:**
- `extract_code_from_response()` — pulls Python from markdown
- `extract_json_from_content()` — pulls JSON from response
- `normalize_vision_endpoint()` — URL normalization
- Model availability checks

**What's good:**
- Battle-tested extraction logic
- Handles edge cases

**What needs change:**
- Nothing significant

**Effort:** None

---

### 2.5 `vision_evaluator.py` — ✅ KEEP (with refactor)

**What it does:**
- `ComparisonVisionClient` for multi-image analysis
- Hybrid VLM + OpenCV measurements
- Structured output parsing

**What's good:**
- Multi-image reasoning works
- OpenCV dimension measurement (optional but useful)
- Prompt construction for comparison

**What needs change:**
- Adapt to new `IterationState` schema
- Extract prompt templates to config
- Ensure JSON output matches new schema

**Effort:** Medium (adapt to new state flow)

---

### 2.6 `viga/memory.py` — ⚠️ REPLACE

**What it does:**
- `IterationContext` dataclass
- `VIGAMemory` with sliding window history

**Why replace:**
- Too simple for LangGraph StateGraph pattern
- Doesn't support checkpointing
- Doesn't match new `IterationState` schema
- No persistence

**Replacement:**
- New `IterationState` TypedDict in Phase I plan
- LangGraph handles state flow and checkpointing
- History compression integrated into state

**Effort:** Medium (new implementation)

---

### 2.7 `viga/agent.py` — ⚠️ REPLACE

**What it does:**
- `GeneratorAgent` — planning + code synthesis
- `VerifierAgent` — vision-based feedback
- `VIGAAgent` — main loop orchestration

**Why replace:**
- Tightly coupled to old memory model
- Doesn't fit LangGraph node pattern (nodes are functions, not classes)
- Loop logic should be in LangGraph edges, not agent class

**What to salvage:**
- Prompt structures for Builder and Evaluator
- The basic generate → execute → verify flow concept

**Replacement:**
- `builder_node()` function
- `evaluator_node()` function
- LangGraph StateGraph for flow control

**Effort:** Medium (rewrite as functions, keep prompt logic)

---

### 2.8 `viga/skills.py` — ⚠️ PARTIAL REPLACE

**What it does:**
- `SkillLibrary` wrapping MCP client calls
- `make_plan()`, `execute_code()`, `investigate()`, `set_camera()`, etc.

**Why partial replace:**
- Some skills are useful (camera, scene info)
- Planning should be part of Builder node, not separate skill
- Skills concept doesn't fit pure MCP tool model

**What to keep:**
- Camera positioning logic
- Scene info formatting

**Effort:** Low (extract useful parts)

---

### 2.9 `orchestrator.py` — ❌ DELETE

**What it does:**
- Legacy "D5" orchestration (Planner → Designer → Executor → Evaluator → Refiner)
- `WorkflowState`, `PlannerAgent`, `DesignerAgent`, etc.

**Why delete:**
- Completely superseded by LangGraph-based design
- Different agent decomposition
- Different state model
- No value in maintaining two orchestration systems

**Effort:** None (just delete)

---

### 2.10 `game_asset_agent.py` + `game_asset_config.py` — ✅ KEEP

**What it does:**
- Complete pipeline: import → cleanup → UV → materials → LODs → FBX export
- Game engine profiles (War Thunder, Unity, etc.)

**What's good:**
- Self-contained
- Well-structured pipeline
- Useful as finalization stage after refinement

**What needs change:**
- Wire into Phase I/II as optional finalization step
- Integrate with artifact logging

**Effort:** Low (integration only)

---

### 2.11 `gpu_config.py` — ✅ KEEP

**What it does:**
- GPU-specific render presets (RTX 3090, 5090)
- Quality profiles (preview, production, final)
- Generates Blender Python to apply settings

**What's good:**
- Useful for diagnostic renders
- Optimized for available hardware

**What needs change:**
- Wire into diagnostic render pipeline

**Effort:** Low

---

### 2.12 `glm_vision.py` — ✅ KEEP

**What it does:**
- Z.AI GLM-4.5V client
- Alternative verifier backend

**What's good:**
- Working implementation
- Good prompt structure

**What needs change:**
- Adapt to new evaluator output schema
- Make optional/swappable

**Effort:** Low

---

### 2.13 Tests — ⚠️ PARTIAL KEEP

**Current tests:**
- `test_code_extraction.py` — ✅ Keep (tests vision_utils)
- `test_viga_agent.py` — ❌ Delete (tests old agent)
- `test_viga_memory.py` — ❌ Delete (tests old memory)
- `test_viga_models.py` — ✅ Keep (tests model adapters)
- `test_vision_utils.py` — ✅ Keep (tests utilities)

**Effort:** Low (delete 2 files)

---

## 3. Implementation Path

### Keep As-Is
- `vision_utils.py`
- `gpu_config.py`
- `game_asset_agent.py` + `game_asset_config.py`
- `glm_vision.py`

### Keep + Extend
- `mcp_client.py` — add new tool methods
- `config/addon.py` — add new handlers
- `viga/modern_models.py` — add role routing

### Keep + Adapt
- `vision_evaluator.py` — adapt to new state schema

### Replace
- `viga/memory.py` → new `IterationState` TypedDict
- `viga/agent.py` → new LangGraph node functions

### Delete
- `orchestrator.py`
- `test_viga_agent.py`
- `test_viga_memory.py`

---

## 4. New Files Needed

| File | Purpose |
|------|---------|
| `src/colossus/state.py` | `IterationState`, `CoordinatorState` schemas |
| `src/colossus/nodes/builder.py` | Builder node function |
| `src/colossus/nodes/evaluator.py` | Evaluator node function |
| `src/colossus/nodes/execute.py` | Execute node (MCP calls) |
| `src/colossus/nodes/finalize.py` | Finalization node |
| `src/colossus/graphs/phase1.py` | Phase I StateGraph |
| `src/colossus/graphs/phase2.py` | Phase II Coordinator graph |
| `src/colossus/workers/pool.py` | Worker pool for Phase II |
| `src/colossus/artifacts.py` | Run folder utilities |
| `src/colossus/prompts/` | Prompt templates (extractable) |
| `tests/test_state.py` | State schema tests |
| `tests/test_nodes.py` | Node function tests |
| `tests/test_phase1_e2e.py` | Phase I end-to-end |
| `tests/test_phase2_e2e.py` | Phase II end-to-end |

---

## 5. Effort Estimate

| Category | Effort |
|----------|--------|
| Keep as-is | 0 hours |
| Keep + extend | 8 hours |
| Keep + adapt | 4 hours |
| Replace (new impl) | 16 hours |
| Delete | 0.5 hours |
| New files | 24 hours |
| Testing | 16 hours |
| **Total** | **~70 hours** |

---

## 6. Recommendation

**Do NOT go fully greenfield.** The existing code has valuable pieces:

1. **MCP client/server** — working, just extend
2. **Model adapters** — working, production-ready
3. **Vision utilities** — battle-tested
4. **Game asset pipeline** — complete, useful for finalization

**DO rewrite:**
1. **Orchestration** — LangGraph replaces everything
2. **State/memory** — new schema for checkpointing
3. **Agent logic** — convert to node functions

This hybrid approach saves ~30 hours vs pure greenfield while giving us a clean architecture.

---

## 7. Suggested New Directory Structure

```
src/
  colossus/                     # New package (cleaner name)
    __init__.py
    state.py                    # IterationState, CoordinatorState
    artifacts.py                # Run folder utilities
    
    nodes/                      # LangGraph node functions
      __init__.py
      builder.py
      evaluator.py
      execute.py
      finalize.py
    
    graphs/                     # Compiled LangGraph graphs
      __init__.py
      phase1.py                 # Inner loop graph
      phase2.py                 # Coordinator graph
    
    workers/                    # Phase II worker pool
      __init__.py
      pool.py
      worker.py
    
    mcp/                        # MCP client (migrated)
      __init__.py
      client.py                 # From mcp_client.py
      tools.py                  # Tool definitions
    
    models/                     # Model adapters (migrated)
      __init__.py
      base.py                   # FoundationModel ABC
      qwen.py                   # Qwen3VL
      gemini.py                 # Gemini3Pro
      router.py                 # Role-based model selection
    
    prompts/                    # Prompt templates
      __init__.py
      builder.py
      evaluator.py
    
    utils/                      # Utilities (migrated)
      __init__.py
      vision.py                 # From vision_utils.py
      code.py                   # Code extraction

  colossus_blender/             # Keep for compatibility, deprecated
    ...

config/
  addon.py                      # Keep + extend

tests/
  test_state.py
  test_nodes.py
  test_mcp.py
  test_models.py
  test_phase1_e2e.py
  test_phase2_e2e.py
```

---

**Decision:** Proceed with hybrid approach. Start Phase I implementation by migrating MCP client and creating new state/nodes.
