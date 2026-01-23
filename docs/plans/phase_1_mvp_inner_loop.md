# Phase I: MVP Inner Loop

**Goal:** A single-attempt, single-worker refinement loop that iterates from a baseline hull toward a target, with structured feedback and checkpointed state.

**Success Criteria:** Run the loop end-to-end on a simple hull refinement task, observe score improvement over iterations, and be able to resume from checkpoint.

**Cross-references:**
- [MASTER_REQUIREMENTS.md](../MASTER_REQUIREMENTS.md) — full requirements
- [phase_2_broad_search.md](./phase_2_broad_search.md) — Phase II (parallel attempts)
- [viga_algorithm.md](../viga/viga_algorithm.md) — VIGA loop theory

---

## 1. Scope

### In Scope (Phase I)
- Single attempt, single Blender instance
- Builder agent (plan + execute via MCP)
- Evaluator agent (vision + structured feedback)
- Shared state via LangGraph StateGraph
- Checkpointing to SQLite (resume after crash)
- Artifact logging (run folder structure)
- Configurable iteration budget and score threshold
- GeoNodes-first actions with bpy escape hatch

### Out of Scope (Phase II+)
- Multiple parallel attempts
- Attempt Coordinator / best-of-N selection
- Worker pool / multi-Blender
- Sentinel (fast guardrails) as separate agent
- Model role splitting (single model serves both Builder and Evaluator for now)

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         RUN SETUP                               │
│  - Create run folder                                            │
│  - Load baseline .blend via MCP                                 │
│  - Initialize IterationState                                    │
│  - Log run config                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ITERATION LOOP                             │
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   BUILDER   │────▶│   EXECUTE   │────▶│  EVALUATOR  │       │
│  │  (plan)     │     │  (MCP)      │     │  (feedback) │       │
│  └─────────────┘     └─────────────┘     └──────┬──────┘       │
│         ▲                                        │              │
│         │         ┌─────────────┐               │              │
│         └─────────│    STATE    │◀──────────────┘              │
│                   │ (checkpoint)│                              │
│                   └─────────────┘                              │
│                                                                 │
│  Stop when: score >= threshold OR iterations >= max OR stagnant │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FINALIZATION                               │
│  - Export final .blend                                          │
│  - Write summary.json                                           │
│  - Optionally run GameAssetAgent for LOD/UV/FBX                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. State Schema

```python
from typing import TypedDict, List, Dict, Any, Literal, Optional

class IterationState(TypedDict):
    # Identity
    run_id: str
    attempt_id: str  # "attempt-000" for Phase I
    iteration: int
    
    # Task context (immutable)
    task_description: str
    reference_images: List[str]
    baseline_path: str
    
    # Scene state
    scene_snapshot: Dict[str, Any]
    current_renders: Dict[str, str]  # view_name → base64
    
    # Last action
    last_plan: str
    last_code: str
    last_execution_result: Dict[str, Any]
    
    # Feedback
    evaluator_feedback: Dict[str, Any]
    current_score: float
    detected_issues: List[str]
    suggested_fixes: List[str]
    
    # History
    iteration_history: List[Dict[str, Any]]
    
    # Control
    status: Literal["running", "converged", "failed", "budget_exhausted"]
    retry_count: int
    
    # Config (logged for reproducibility)
    config: Dict[str, Any]
```

---

## 4. MCP Tools Required

| Tool | Purpose | Priority | Status |
|------|---------|----------|--------|
| `execute_code` | Run arbitrary bpy Python | P0 | ✅ Exists |
| `get_scene_info` | Scene state snapshot | P0 | ✅ Exists |
| `get_viewport_screenshot` | Capture current view | P0 | ✅ Exists |
| `reset_to_baseline` | Load baseline .blend | P0 | ❌ Implement |
| `set_camera_pose` | Position camera for diagnostic views | P1 | ❌ Implement |
| `get_diagnostic_renders` | Capture front/side/top/iso pack | P1 | ❌ Implement |
| `geonode_create_group` | Create new GeoNode group | P1 | ❌ Implement |
| `geonode_add_node` | Add node to group | P1 | ❌ Implement |
| `geonode_connect` | Connect node sockets | P1 | ❌ Implement |
| `geonode_set_param` | Set node parameter | P1 | ❌ Implement |
| `export_blend` | Save current scene | P0 | ❌ Implement |

**Phase I minimum:** `execute_code`, `get_scene_info`, `get_viewport_screenshot`, `reset_to_baseline`, `export_blend`. GeoNode tools can be deferred if we use bpy scripts that manipulate GeoNodes.

---

## 5. Agent Definitions

### 5.1 Builder Agent

**Role:** Plan what to do next, then produce executable actions.

**Inputs (from state):**
- `task_description`
- `reference_images`
- `scene_snapshot`
- `current_renders`
- `detected_issues`
- `suggested_fixes`
- `iteration_history` (compressed)

**Outputs (to state):**
- `last_plan` — natural language description of intended changes
- `last_code` — executable bpy Python (or GeoNode tool calls)

**Prompt structure:**
```
You are a Blender modeling agent refining a 3D hull toward a reference.

TASK: {task_description}

CURRENT SCENE STATE:
{scene_snapshot}

ISSUES DETECTED BY EVALUATOR:
{detected_issues}

SUGGESTED FIXES:
{suggested_fixes}

ITERATION HISTORY:
{iteration_history}

Produce:
1. PLAN: What you will change and why
2. CODE: Executable Blender Python to make those changes

Focus on fixing the most impactful issues first.
Prefer modifying existing geometry/parameters over starting fresh.
```

### 5.2 Evaluator Agent

**Role:** Analyze the scene and provide structured feedback. Does NOT execute.

**Inputs (from state):**
- `task_description`
- `reference_images`
- `current_renders`
- `scene_snapshot`

**Outputs (to state):**
- `evaluator_feedback` — full structured response
- `current_score` — 0.0 to 1.0
- `detected_issues` — list of problems found
- `suggested_fixes` — list of specific fixes

**Prompt structure:**
```
You are a 3D modeling evaluator comparing a Blender scene to a reference.

TASK: {task_description}

REFERENCE IMAGES: [attached]
CURRENT RENDERS: [attached]

SCENE STATE:
{scene_snapshot}

Analyze the current state and output JSON:
{
  "overall_score": 0.0-1.0,
  "category_scores": {
    "shape_accuracy": 0.0-1.0,
    "proportions": 0.0-1.0,
    "detail_level": 0.0-1.0,
    "surface_quality": 0.0-1.0
  },
  "detected_issues": [
    "Issue 1 with specifics",
    "Issue 2 with specifics"
  ],
  "suggested_fixes": [
    "Specific fix 1 with parameters",
    "Specific fix 2 with parameters"
  ],
  "positive_aspects": [
    "What's working well"
  ],
  "is_complete": true/false
}

Check for these gross failures:
- Position: floating, below ground, off-center, intersecting
- Scale: too small, too large, wrong proportions
- Orientation: upside down, wrong facing direction
- Geometry: missing faces, inverted normals, non-manifold
- Reference match: wrong shape, missing features, extra features
```

---

## 6. LangGraph Implementation

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

def builder_node(state: IterationState) -> IterationState:
    """Generate plan and code based on current state + feedback."""
    prompt = build_builder_prompt(state)
    response = model.generate(prompt, images=state["current_renders"].values())
    plan, code = parse_builder_response(response)
    return {
        **state,
        "last_plan": plan,
        "last_code": code,
    }

def execute_node(state: IterationState) -> IterationState:
    """Execute the code via MCP and capture results."""
    result = mcp_client.execute_code(state["last_code"])
    scene = mcp_client.get_scene_info()
    renders = mcp_client.get_diagnostic_renders()
    return {
        **state,
        "last_execution_result": result,
        "scene_snapshot": scene,
        "current_renders": renders,
    }

def evaluator_node(state: IterationState) -> IterationState:
    """Analyze scene and provide structured feedback."""
    prompt = build_evaluator_prompt(state)
    images = list(state["current_renders"].values()) + state["reference_images"]
    response = model.generate(prompt, images=images)
    feedback = parse_evaluator_response(response)
    
    # Update history (sliding window)
    history_entry = {
        "iteration": state["iteration"],
        "plan": state["last_plan"],
        "score": feedback["overall_score"],
        "issues_count": len(feedback["detected_issues"]),
    }
    history = state["iteration_history"][-4:] + [history_entry]  # keep last 5
    
    return {
        **state,
        "evaluator_feedback": feedback,
        "current_score": feedback["overall_score"],
        "detected_issues": feedback["detected_issues"],
        "suggested_fixes": feedback["suggested_fixes"],
        "iteration": state["iteration"] + 1,
        "iteration_history": history,
    }

def should_continue(state: IterationState) -> str:
    """Decide whether to continue iterating."""
    config = state["config"]
    
    if state["current_score"] >= config["score_threshold"]:
        return "converged"
    if state["iteration"] >= config["max_iterations"]:
        return "budget_exhausted"
    if state["retry_count"] >= config["max_retries"]:
        return "failed"
    # Stagnation detection
    if len(state["iteration_history"]) >= 3:
        recent_scores = [h["score"] for h in state["iteration_history"][-3:]]
        if max(recent_scores) - min(recent_scores) < 0.02:
            return "stagnant"
    return "continue"

# Build graph
builder = StateGraph(IterationState)
builder.add_node("builder", builder_node)
builder.add_node("execute", execute_node)
builder.add_node("evaluator", evaluator_node)
builder.add_node("finalize", finalize_node)

builder.add_edge(START, "builder")
builder.add_edge("builder", "execute")
builder.add_edge("execute", "evaluator")
builder.add_conditional_edges(
    "evaluator",
    should_continue,
    {
        "continue": "builder",
        "converged": "finalize",
        "budget_exhausted": "finalize",
        "stagnant": "finalize",
        "failed": "finalize",
    }
)
builder.add_edge("finalize", END)

# Compile with checkpointing
checkpointer = SqliteSaver.from_conn_string("runs/phase1.db")
graph = builder.compile(checkpointer=checkpointer)
```

---

## 7. Artifact Structure

```
runs/
  {timestamp}_{task_slug}/
    run.json                    # Run config, model, thresholds
    baseline.blend              # Starting state
    attempt-000/
      config.json               # Attempt-specific config
      iterations/
        iter-000/
          plan.txt              # Builder's plan
          code.py               # Executed code
          execution.json        # Result + any errors
          renders/
            front.png
            side.png
            top.png
            iso.png
          feedback.json         # Evaluator's structured output
        iter-001/
          ...
      final_score.json          # Last score + status
      final.blend               # Final scene state
    summary.json                # Run summary
```

---

## 8. Test Plan (TDD)

### 8.1 Unit Tests

| Test | What it validates |
|------|-------------------|
| `test_state_schema` | IterationState serializes/deserializes correctly |
| `test_builder_prompt_construction` | Prompt includes all required context |
| `test_evaluator_response_parsing` | JSON parsing handles edge cases |
| `test_checkpoint_save_restore` | Can resume from saved state |
| `test_history_compression` | Sliding window works correctly |
| `test_stop_conditions` | All stop conditions trigger correctly |

### 8.2 Integration Tests

| Test | What it validates |
|------|-------------------|
| `test_mcp_execute_code` | Can run bpy code via MCP |
| `test_mcp_get_scene_info` | Scene info is valid JSON |
| `test_mcp_get_screenshot` | Screenshot returns valid image |
| `test_mcp_reset_baseline` | Scene resets to known state |
| `test_builder_to_evaluator_handoff` | State flows correctly |
| `test_full_iteration_cycle` | One complete iteration works |

### 8.3 End-to-End Tests

| Test | What it validates |
|------|-------------------|
| `test_simple_cube_refinement` | Loop runs on trivial task |
| `test_hull_proportions_task` | Loop improves hull proportions |
| `test_checkpoint_resume` | Can stop and resume mid-run |
| `test_score_improvement` | Score increases over iterations |
| `test_artifact_logging` | All artifacts written correctly |

---

## 9. Implementation Order

### Week 1: Foundation
1. [ ] Define `IterationState` TypedDict
2. [ ] Implement `reset_to_baseline` MCP tool
3. [ ] Implement `export_blend` MCP tool
4. [ ] Create run folder structure utilities
5. [ ] Write unit tests for state schema

### Week 2: Agents
1. [ ] Implement Builder prompt construction
2. [ ] Implement Evaluator prompt construction
3. [ ] Implement response parsers (plan/code extraction, JSON parsing)
4. [ ] Write unit tests for prompts and parsers
5. [ ] Test with mock model responses

### Week 3: Graph
1. [ ] Implement LangGraph nodes (builder, execute, evaluator, finalize)
2. [ ] Implement `should_continue` routing
3. [ ] Add SqliteSaver checkpointing
4. [ ] Write integration tests for node handoffs
5. [ ] Test checkpoint save/restore

### Week 4: E2E
1. [ ] Create simple test baseline (cube or basic hull)
2. [ ] Run full loop on test task
3. [ ] Debug and fix issues
4. [ ] Validate artifact logging
5. [ ] Document any model-specific quirks

---

## 10. Success Metrics

| Metric | Target |
|--------|--------|
| Loop completes without crash | 100% |
| Checkpoint resume works | 100% |
| Score improves over iterations | >80% of runs |
| Artifacts fully logged | 100% |
| Time per iteration | <60s with local model |

---

## 11. Open Decisions (to be resolved during implementation)

| Decision | Options | Leaning |
|----------|---------|---------|
| GeoNodes vs bpy scripts | GeoNodes-first / bpy-first / hybrid | Hybrid: bpy that creates/modifies GeoNodes |
| Diagnostic view count | 4 (front/side/top/iso) / 6 / 8 | Start with 4 |
| History window size | 3 / 5 / 10 | 5 |
| Stagnation threshold | 0.01 / 0.02 / 0.05 | 0.02 |

---

**Next:** After Phase I is working, proceed to [Phase II: Broad Search](./phase_2_broad_search.md).
