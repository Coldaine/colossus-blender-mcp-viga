# Colossus Blender MCP: Master Requirements Document

**Version:** 1.0  
**Date:** January 2026  
**Purpose:** Exhaustive requirements specification for the multi-agent 3D modeling system

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Capability Requirements](#3-capability-requirements)
   - 3.1 Blender Integration (MCP Bridge)
   - 3.2 Agent Memory & State Management
   - 3.3 Multi-Agent Orchestration
   - 3.4 Vision & Verification
   - 3.5 Parallel Execution & Broad Search
   - 3.6 Artifact Persistence & Reproducibility
   - 3.7 Model Backend Integration
4. [End-to-End Workflow](#4-end-to-end-workflow)
5. [Research & Solutions](#5-research--solutions)
6. [Implementation Priorities](#6-implementation-priorities)
7. [Open Questions](#7-open-questions)

---

## 1. Executive Summary

Colossus Blender MCP is a **multi-agent, stateful, vision-guided 3D modeling system** that uses the VIGA (Vision-as-Inverse-Graphics Analysis-by-Synthesis) algorithm to iteratively create and refine 3D assets in Blender.

### 2026 Integration Assumption: MCP as the “Central Nervous System”

This project uses MCP as the boundary between the **agent runtime** and **Blender/tooling**:

- **Blender runs an MCP server** (the environment).
- **Agents run externally** (the client), connecting via MCP.

Important scope clarification:

- MCP is the integration protocol for controlling Blender and related tools.
- Not everything in the system needs to be “an MCP.” Internal coordination/memory/orchestration can remain in-process; MCP is for crossing the boundary into Blender/tool servers.

Optional “dual-server” pattern (advanced, not required for MVP):

- **Primary MCP Server:** BlenderMCP (scene management, code execution, asset generation/import)
- **Visual/Viewport MCP Server:** a server that exposes high-frequency viewport/UI capture tools

Note: If we don’t adopt a separate Visual server, the Primary server can still provide screenshots; the “dual-server” concept is simply about splitting responsibilities for throughput and reliability.

### Core Complexity Acknowledgment

This system is **not a simple script executor**. It is an agentic system comparable in complexity to Gemini CLI, requiring:

- **Stateful persistence** across sessions
- **Multi-agent coordination** (Orchestrator + Workers)
- **Hierarchical memory** (global, run, attempt, iteration)
- **Parallel execution** with isolated environments
- **History compression** to manage token limits
- **Artifact tracking** for reproducibility

---

## 2. System Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER / CLI / API                                  │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AGENT RUNTIME (MCP CLIENT + ROUTER)                       │
│                                                                             │
│  ┌──────────────────────────┐      ┌──────────────────────────┐            │
│  │ Attempt Coordinator       │      │ Shared Memory + Artifacts │            │
│  │ (Broad Search)            │      │ (Run/Attempt/Iter tiers)  │            │
│  └──────────────┬───────────┘      └──────────────┬───────────┘            │
│                 │                                 │                        │
│                 ▼                                 ▼                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ VIGA Loop (per Attempt / Worker)                                      │  │
│  │  Plan → Act (MCP Tools) → Observe (Vision+Scene) → Fix → Repeat        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MCP SERVER MESH (ENV)                               │
│                                                                             │
│  Primary: BlenderMCP (scene/tools)           Visual: Screen/Vision MCP       │
│  ┌──────────────┐  ┌──────────────┐        ┌──────────────────────────┐     │
│  │ Blender:9876 │  │ Blender:9877 │        │ viewport/ui capture tools │     │
│  └──────────────┘  └──────────────┘        └──────────────────────────┘     │
│                                                                             │
│  Optional: Other MCP tools (Substance/Unreal/etc)                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Agent Roles

| Agent | Responsibility | Current Implementation | Gap |
|-------|---------------|------------------------|-----|
| **Attempt Coordinator** | Spawns attempts, collects scores, selects best | ❌ Not implemented | High |
| **Builder (Plan+Act)** | Produces tool actions and applies them in Blender | ⚠️ Partially (VIGA Generator + execute_code) | Needs MCP tool-first actions |
| **Verifier (Vision+Metrics)** | Evaluates progress and outputs actionable feedback | ✅ Verifier path exists | Needs strict JSON schema |
| **Sentinel (Fast Guardrails)** | Detects obvious visual failures (floating/scale/framing) and applies quick fixes | ❌ Not implemented | Optional (P1) |
| **Memory/Artifacts Manager** | Persistent state + run folder structure | ❌ Only `VIGAMemory` | Critical |
| **Game Asset Agent** | Mesh → game-ready export pipeline (LODs/UV/FBX) | ✅ `GameAssetAgent` | Integrate as finalization |
| **GLM Vision** | Alternative verifier backend | ✅ `GLMVisionClient` | Optional |
| **GPU Configurator** | Render preset selection for diagnostics/final | ✅ `GPUConfigurator` | Wire into camera pack |

Design intent: roles are **composable** and **configurable per run** (which roles are enabled, which models back them, cadence settings) and all decisions are logged in run artifacts.

---

## 3. Capability Requirements

### 3.1 Blender Integration (MCP Tooling)

**What we need:** The agent must control Blender via MCP tools. A dual-server setup is optional.

- **Primary MCP Server (BlenderMCP):** scene management, Geometry Nodes graph construction, asset import/generation, renders.
- **Visual MCP Server (screen-vision):** high-frequency viewport/UI oversight to enable a reliable vision-action loop.

#### 3.1.1 Current State

| Capability | File | Status |
|------------|------|--------|
| Execute Python code | `mcp_client.py` | ✅ Working |
| Get scene info | `mcp_client.py` | ✅ Working |
| Capture viewport screenshot | `mcp_client.py` | ✅ Working |
| Clear scene | `mcp_client.py` | ✅ Working |
| Reset to baseline | N/A | ❌ Not implemented |
| PolyHaven integration | `addon.py` | ✅ Working |
| Sketchfab integration | `addon.py` | ✅ Working |
| Hyper3D Rodin generation | `addon.py` | ✅ Working |

#### 3.1.2 Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| **BL-00** | Treat MCP as the system boundary (“CNS”) | P0 | Agent is external MCP client |
| **BL-01** | Primary MCP: BlenderMCP for scene + assets | P0 | Base: current addon implementation |
| **BL-01a** | Optional: Visual/Viewport server for oversight | P2 | Can be separate or folded into primary |
| **BL-02** | Implement `reset_to_baseline(baseline_id)` skill | P0 | Required for attempt isolation |
| **BL-03** | Support multiple simultaneous Blender instances | P1 | One Blender per worker |
| **BL-04** | Port management for parallel Blenders | P1 | Port 9876, 9877, 9878... |
| **BL-05** | Diagnostic camera pack (front/side/top/iso) | P1 | Deterministic comparison |
| **BL-06** | Standardized render settings presets | P2 | Preview vs final |
| **BL-07** | GeoNodes-first workflow support | P0 | Build/modify node trees via tools |
| **BL-09** | Scene “safety” corrective tools | P1 | e.g., transform_to_floor, normalize_scale |

Non-requirement (explicitly out of scope):

- Generative 3D “prompt-to-mesh” asset creation is **not** a goal for this project.

#### 3.1.3 MCP Server Roles (Target)

| Server Role | Implementation | Purpose |
|-------------|----------------|---------|
| **Primary Blender MCP** | Current addon implementation | Scene ops, asset tools, execution |
| **Visual MCP** | Add-on or external server | Frequent viewport/UI capture + checks |

**Decision:** Keep the current primary server, but explicitly design for a dual-server topology and an MCP “tool router” so multiple tool servers can be used in one run.

---

### 3.2 Agent Memory & State Management

**What we need:** Hierarchical, persistent memory that survives crashes, supports compression, and enables cross-session learning.

#### 3.2.1 Current State (CRITICAL GAP)

The current `VIGAMemory` is a **toy implementation**:

```python
class VIGAMemory:
    def __init__(self, window_size: int = 3):
        self.history: List[IterationContext] = []  # Just a Python list!
        self.window_size = window_size
```

**Problems:**
- No persistence (lost on crash/restart)
- No hierarchical tiers
- No compression
- No cross-session memory
- No attempt isolation

#### 3.2.2 Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| **MEM-01** | Hierarchical memory tiers | P0 | Global → Run → Attempt → Iteration |
| **MEM-02** | Session persistence to disk | P0 | Resume after crash |
| **MEM-03** | Memory window with sliding context | P0 | Already have (window_size=3) |
| **MEM-04** | History compression | P1 | Compress old iterations into summaries |
| **MEM-05** | Cross-session learning | P2 | What worked on previous runs |
| **MEM-06** | Attempt isolation | P0 | Each attempt has its own memory branch |
| **MEM-07** | Checkpoint serialization | P0 | Save/restore full state |

#### 3.2.3 Memory Tier Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GLOBAL MEMORY                               │
│  - Model configuration                                          │
│  - Default system prompts                                       │
│  - Learned patterns (optional future)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     RUN MEMORY                                   │
│  - Task specification                                           │
│  - Reference images                                             │
│  - Baseline ID                                                  │
│  - Run configuration                                            │
│  - Start timestamp                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ ATTEMPT 0       │ │ ATTEMPT 1       │ │ ATTEMPT N       │
│ - Strategy      │ │ - Strategy      │ │ - Strategy      │
│ - Final score   │ │ - Final score   │ │ - Final score   │
│ - Selected?     │ │ - Selected?     │ │ - Selected?     │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ ITERATIONS      │ │ ITERATIONS      │ │ ITERATIONS      │
│ [0] plan/code   │ │ [0] plan/code   │ │ [0] plan/code   │
│ [1] plan/code   │ │ [1] plan/code   │ │ [1] plan/code   │
│ [2] plan/code   │ │ [2] plan/code   │ │ [2] plan/code   │
│ ...             │ │ ...             │ │ ...             │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

#### 3.2.4 Research: Memory/State Solutions

| Solution | What It Provides | Fit |
|----------|------------------|-----|
| **LangGraph Checkpointer** | Checkpoint save/restore, SQLite/Postgres backends | ✅ Best fit |
| **LangGraph InMemorySaver** | In-memory checkpoints with optional persistence | ✅ Good starting point |
| **LangGraph PersistentDict** | File-backed persistent dictionary | ✅ Useful for run state |
| **MemGPT** | Long-term memory with retrieval | ⚠️ Overkill for now |
| **Custom JSON files** | Simple persistence | ⚠️ Reinventing wheel |

**Recommended Approach:** Use LangGraph's checkpointing infrastructure:

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import InMemorySaver

# For development:
checkpointer = InMemorySaver()

# For production:
checkpointer = SqliteSaver.from_conn_string("runs/colossus.db")

# Compile graph with checkpointer
graph = builder.compile(checkpointer=checkpointer)
```

---

### 3.3 Multi-Agent Orchestration

**What we need:** A coordinator that manages the lifecycle of N parallel attempts, dispatches work, and selects the best result.

#### 3.3.1 Current State

| Component | File | Status |
|-----------|------|--------|
| Planner Agent | `orchestrator.py` | ✅ Legacy D5 |
| Designer Agent | `orchestrator.py` | ✅ Legacy D5 |
| Executor Agent | `orchestrator.py` | ✅ Legacy D5 |
| Evaluator Agent | `orchestrator.py` | ✅ Legacy D5 |
| Refiner Agent | `orchestrator.py` | ✅ Legacy D5 |
| VIGA Generator | `viga/agent.py` | ✅ Implemented |
| VIGA Verifier | `viga/agent.py` | ✅ Implemented |
| Attempt Coordinator | N/A | ❌ Not implemented |

**Note:** We have TWO orchestration systems:
1. `orchestrator.py` - Legacy "D5" pattern (Planner→Designer→Executor→Evaluator→Refiner)
2. `viga/agent.py` - VIGA loop (Generator→Execute→Verify→Memory)

These need to be unified.

#### 3.3.2 Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| **ORCH-01** | Attempt Coordinator manages N attempts | P0 | Broad Search strategy |
| **ORCH-02** | Worker pool for parallel execution | P1 | One Blender per worker |
| **ORCH-03** | Attempt job queue | P1 | Dispatch attempts to workers |
| **ORCH-04** | Best attempt selection | P0 | Max score wins |
| **ORCH-05** | Stop conditions | P0 | Score threshold, max attempts, timeout |
| **ORCH-06** | Unified agent architecture | P1 | Merge D5 + VIGA |
| **ORCH-07** | Inter-agent communication protocol | P1 | How agents share state |

#### 3.3.3 Agent Communication Patterns

**Decision: Shared State via LangGraph StateGraph**

All agents within an attempt share a single `IterationState` that persists across the loop:

```python
class IterationState(TypedDict):
    # Identity
    run_id: str
    attempt_id: str
    iteration: int
    
    # Task context (immutable for attempt)
    task_description: str
    reference_images: List[str]  # base64 or paths
    baseline_id: str
    
    # Current scene state
    scene_snapshot: Dict[str, Any]  # from get_scene_info
    current_renders: Dict[str, str]  # view_name → base64
    
    # Last action taken
    last_plan: str
    last_code: str
    last_execution_result: Dict[str, Any]
    
    # Feedback from evaluators
    evaluator_feedback: Dict[str, Any]  # structured JSON
    current_score: float
    detected_issues: List[str]
    suggested_fixes: List[str]
    
    # History (sliding window for token management)
    iteration_history: List[Dict[str, Any]]  # compressed summaries
    
    # Control
    status: Literal["running", "converged", "failed", "budget_exhausted"]
    retry_count: int
```

**Context Persistence Model:**

1. **Within iteration:** State passed through LangGraph nodes (Builder → Evaluator → Builder)
2. **Across iterations:** State checkpointed to disk after each iteration via `SqliteSaver`
3. **Across attempts:** Parent `RunState` tracks all attempts; each attempt has isolated `IterationState`
4. **Across runs:** Run artifacts saved to `runs/` folder; can be replayed

**How agents share context:**
- Builder reads `evaluator_feedback`, `detected_issues`, `suggested_fixes` from state
- Builder writes `last_plan`, `last_code`, `last_execution_result` to state
- Evaluator reads `current_renders`, `scene_snapshot`, `task_description` from state
- Evaluator writes `evaluator_feedback`, `current_score`, `detected_issues`, `suggested_fixes` to state

No message passing needed within an attempt; all coordination is via shared state.

#### 3.3.4 Research: Orchestration Frameworks

| Framework | Features | Fit |
|-----------|----------|-----|
| **LangGraph** | StateGraph, Checkpointing, Subgraphs, Parallel execution | ✅ Best fit |
| **AutoGen** | Multi-agent conversations | ⚠️ Chatbot-focused |
| **CrewAI** | Role-based agents | ⚠️ Limited customization |
| **Custom asyncio** | Full control | ⚠️ More work |

**Recommended Approach:** Use LangGraph StateGraph:

```python
from langgraph.graph import StateGraph, START, END
from langgraph.graph.graph import CompiledStateGraph

class CoordinatorState(TypedDict):
    task: str
    baseline_id: str
    attempts: List[AttemptResult]
    best_score: float
    best_attempt_id: str
    status: str

def spawn_attempts(state: CoordinatorState) -> CoordinatorState:
    # Create N attempt jobs
    ...

def collect_results(state: CoordinatorState) -> CoordinatorState:
    # Wait for all attempts, select best
    ...

builder = StateGraph(CoordinatorState)
builder.add_node("spawn", spawn_attempts)
builder.add_node("collect", collect_results)
builder.add_edge(START, "spawn")
builder.add_edge("spawn", "collect")
builder.add_edge("collect", END)

coordinator = builder.compile(checkpointer=checkpointer)
```

---

### 3.4 Vision & Verification

**What we need:** VLM-powered scene analysis that produces structured, actionable feedback for the Generator.

#### 3.4.0 The 2026 “Vision-Action” Loop (Non-negotiable)

After every major operation (or batch of ops), the loop must:

1. **Builder** executes actions via MCP tools
2. **Evaluator** captures viewport and scene state
3. **Evaluator** detects issues and provides structured feedback (does NOT execute corrections)
4. **Builder** receives feedback and executes corrections
5. Repeat until convergence or budget exhausted

**Critical architecture principle:** Evaluation agents (Verifier, Sentinel) **only provide feedback**. Execution agents (Builder) **only execute actions**. This separation enables:
- Clean logging of what was detected vs what was done
- Easy swapping of evaluator models
- Testable feedback → action mapping

#### 3.4.0.1 Gross Failure Detection Checklist

The Evaluator should check for (via prompt, not hardcoded):

| Category | Failures to Detect |
|----------|--------------------|
| **Position** | Object floating in air, object below ground plane, object far from origin, object intersecting other objects |
| **Scale** | Object too small to see, object absurdly large, proportions wrong (too tall/wide/deep) |
| **Orientation** | Object upside down, object rotated incorrectly, object facing wrong direction |
| **Framing** | Camera not pointed at subject, subject clipped by camera, subject too small in frame, subject off-center |
| **Geometry** | Missing faces, inverted normals, non-manifold edges, disconnected vertices, self-intersecting geometry |
| **Topology** | Excessive polygon count, insufficient detail in key areas, n-gons where quads needed |
| **Materials** | Missing materials, default gray material, incorrect material assignment, texture stretching |
| **Lighting** | Scene too dark, scene overexposed, harsh shadows hiding detail, no shadows at all |
| **Reference Match** | Wrong overall shape, missing features from reference, extra features not in reference |
| **Structural** | Hull not watertight, deck not level, symmetry broken, features not aligned |

This list is prompt-driven and extensible. The Evaluator outputs which issues were detected; the Builder decides how to fix them.

This cadence must be **configurable, testable, and logged** (what cadence ran, when, and with which models/settings).

#### 3.4.1 Current State

| Capability | File | Status |
|------------|------|--------|
| Screenshot capture | `mcp_client.py` | ✅ Working |
| VLM inference (Qwen3-VL) | `modern_models.py` | ✅ Working |
| VLM inference (Gemini) | `modern_models.py` | ✅ Working |
| Structured evaluation | `vision_evaluator.py` | ✅ Working |
| OpenCV hybrid analysis | `vision_evaluator.py` | ✅ Working |
| Blueprint comparison | `vision_evaluator.py` | ✅ Working |

#### 3.4.2 Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| **VIS-01** | Structured JSON output from verifier | P0 | score, issues, suggestions |
| **VIS-02** | Multi-image comparison | P1 | Reference vs render |
| **VIS-03** | Deterministic camera poses | P1 | Same angles across attempts |
| **VIS-04** | Separate “sentinel” checks vs “director” critique | P1 | Fast gross-failure loop |
| **VIS-05** | Quantitative measurements | P2 | OpenCV dimensions |
| **VIS-06** | Corrective action mapping | P1 | issue → tool action template |

#### 3.4.3 Structured Verifier Output Schema

```python
@dataclass
class VerifierOutput:
    overall_score: float  # 0.0 - 1.0
    is_complete: bool
    scores: Dict[str, float]  # composition, lighting, materials, goal_match
    issues: List[str]  # What's wrong
    suggestions: List[str]  # Specific fixes with parameters
    positive_aspects: List[str]  # What's good
    
    # For scoring
    def to_dict(self) -> Dict[str, Any]: ...
```

---

### 3.5 Parallel Execution & Broad Search

**What we need:** Run N attempts simultaneously, each in an isolated Blender instance, and select the best result.

Key design requirement: attempt isolation must be a deliberate choice (separate Blender per worker vs reload baseline per attempt) and must be recorded in run artifacts.

#### 3.5.1 Current State

No parallel execution implemented. Single-threaded VIGA loop only.

#### 3.5.2 Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| **PAR-01** | Run N attempts from same baseline | P1 | Broad Search strategy |
| **PAR-02** | One Blender instance per worker | P1 | Isolation |
| **PAR-03** | Worker pool with job queue | P1 | Scalable |
| **PAR-04** | Unique artifact folders per attempt | P0 | No collisions |
| **PAR-05** | Score-based selection | P0 | Best of N |
| **PAR-06** | Strategy variation | P2 | Different prompts per attempt |

#### 3.5.3 Parallelization Architecture

```
Coordinator
    │
    ├─▶ Worker Pool
    │       │
    │       ├─▶ Worker 0 ─▶ Blender:9876 ─▶ Attempt 0
    │       ├─▶ Worker 1 ─▶ Blender:9877 ─▶ Attempt 1
    │       ├─▶ Worker 2 ─▶ Blender:9878 ─▶ Attempt 2
    │       └─▶ Worker N ─▶ Blender:987N ─▶ Attempt N
    │
    └─▶ Results Collector ─▶ Best Selection
```

#### 3.5.4 Research: Parallelization Approaches

| Approach | Pros | Cons |
|----------|------|------|
| **asyncio.gather** | Simple, same process | GIL limits, shared memory |
| **multiprocessing.Pool** | True parallelism | IPC overhead |
| **concurrent.futures** | Clean API | Same as multiprocessing |
| **Ray** | Distributed, fault-tolerant | Heavy dependency |
| **LangGraph Send** | Native parallel nodes | Requires graph restructure |

**Recommendation:** Start with `concurrent.futures.ProcessPoolExecutor` for local, consider Ray for remote workers.

---

### 3.6 Artifact Persistence & Reproducibility

**What we need:** Every attempt must be inspectable, comparable, and replayable.

#### 3.6.1 Current State

No artifact persistence implemented.

#### 3.6.2 Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| **ART-01** | Run folder structure | P0 | `runs/<timestamp>_<task>/` |
| **ART-02** | run.json metadata | P0 | Task, baseline, models, config |
| **ART-03** | attempt.json per attempt | P0 | Score, strategy, status |
| **ART-04** | iteration artifacts | P0 | plan, code, renders, feedback |
| **ART-05** | Deterministic render pack | P1 | front/side/top/iso |
| **ART-06** | Replay capability | P2 | Re-run from checkpoint |

#### 3.6.3 Folder Structure

```
runs/
  2026-01-22T15-40-11Z_battleship_hull/
    run.json                      # Run metadata
    baseline.blend                # Starting state
    attempts/
      attempt-000/
        attempt.json              # Attempt metadata
        strategy.txt              # Strategy prompt variant
        iterations/
          iter-000/
            plan.txt              # Generator plan
            code.py               # Generated code
            execution.json        # Exec result + errors
            renders/
              front.png
              side.png
              top.png
              iso.png
            verifier.json         # Structured feedback
            generator_raw.txt     # Full LLM response
            verifier_raw.txt      # Full VLM response
          iter-001/
            ...
        final_score.json
        final_scene.blend
      attempt-001/
        ...
    best_attempt.json             # Which attempt won
    summary.json                  # Run summary
```

---

### 3.7 Model Backend Integration

**What we need:** Flexible model backends for generation and verification, with fallback chains.

#### 3.7.1 Current State

| Model | Provider | File | Status |
|-------|----------|------|--------|
| Qwen3-VL-8B | Local llama.cpp | `modern_models.py` | ✅ Working |
| Qwen3-VL-30B | Local llama.cpp | `modern_models.py` | ✅ Working |
| Gemini 3 Pro | Google AI Studio | `modern_models.py` | ✅ Working |
| Mock Model | Testing | `modern_models.py` | ✅ Working |

#### 3.7.2 Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| **MOD-01** | OpenAI-compatible endpoint | P0 | Already have |
| **MOD-02** | Multi-image support | P0 | Already have |
| **MOD-03** | Fallback chain | P1 | Try local, fallback to API |
| **MOD-04** | Different models per role | P2 | Generator vs Verifier |
| **MOD-05** | Model health check | P2 | Verify before use |

#### 3.7.3 Model Role Strategy (Jan 2026)

Principle: model assignment is **configurable per run** and recorded in artifacts.

Suggested defaults (can be swapped):

| Role | Typical Strength | Notes |
|------|------------------|-------|
| **Planner/Architect** | Long-horizon planning with huge context | Optional role split from Builder |
| **Builder/Executor/Fixer** | Precise debugging and corrective edits | Handles tracebacks/topology fixes |
| **Verifier/Art Director** | Multimodal critique and rubric scoring | Produces actionable feedback |
| **Sentinel** | Fast guardrails + obvious failure detection | Can be a cheaper/faster model |

Requirement: for every run/attempt/iteration, we must log:

- which model served each role
- which prompts/policies were active (cadence, thresholds)
- any fallbacks or retries

---

## 4. End-to-End Workflow

### 4.1 Complete Run Workflow

```
1. USER INPUT
   │
   ├─ Task: "Create a WWII battleship hull with correct proportions"
   ├─ Reference images (optional)
   ├─ Baseline: "empty_scene.blend"
   └─ Config: attempts=3, iterations=5, threshold=0.85

2. RUN INITIALIZATION
   │
   ├─ Create run folder: runs/2026-01-22T15-40-11Z_battleship/
   ├─ Save run.json (metadata)
   ├─ Copy baseline.blend to run folder
   └─ Initialize StateManager

3. COORDINATOR STARTUP
   │
   ├─ Load run state
   ├─ Spawn worker pool (N workers)
   ├─ Start N Blender instances (ports 9876-987X)
   └─ Dispatch attempt jobs

4. ATTEMPT EXECUTION (per worker, in parallel)
   │
   ├─ 4.1 RESET BASELINE
   │       └─ Load baseline.blend via MCP
   │
   ├─ 4.2 VIGA LOOP (iterations)
   │       │
   │       ├─ GENERATOR
   │       │   ├─ Build context from memory window
   │       │   ├─ Generate plan
   │       │   ├─ Synthesize Blender code
   │       │   └─ Output: plan + code
   │       │
   │       ├─ EXECUTE
   │       │   ├─ Send code to Blender MCP
   │       │   ├─ Execute in Blender
   │       │   ├─ Check for errors
   │       │   └─ Output: success/error + scene state
   │       │
   │       ├─ FAST FIX (if error)
   │       │   ├─ Retry up to 3 times
   │       │   ├─ Show error to Generator
   │       │   └─ Get fixed code
   │       │
   │       ├─ VERIFY
   │       │   ├─ Initialize camera viewpoint
   │       │   ├─ Capture diagnostic renders (4 views)
   │       │   ├─ Send to VLM for analysis
   │       │   ├─ Parse structured output
   │       │   └─ Output: score + issues + suggestions
   │       │
   │       ├─ MEMORY UPDATE
   │       │   ├─ Store iteration context
   │       │   ├─ Compress old iterations if needed
   │       │   └─ Checkpoint to disk
   │       │
   │       └─ CONVERGENCE CHECK
   │           ├─ If score >= threshold: stop
   │           ├─ If max iterations: stop
   │           └─ Else: continue loop
   │
   └─ 4.3 ATTEMPT COMPLETE
           ├─ Save final score
           ├─ Save final scene.blend
           └─ Report to Coordinator

5. RESULT COLLECTION
   │
   ├─ Wait for all attempts to complete
   ├─ Collect final scores
   ├─ Select best attempt (max score)
   └─ Record in best_attempt.json

6. RUN COMPLETE
   │
   ├─ Save summary.json
   ├─ Shut down worker pool
   ├─ Shut down Blender instances
   └─ Return best attempt result
```

### 4.2 Parallel Comparison Flow

```
        ┌─────────────────────────────────────────────────────────┐
        │                    COORDINATOR                          │
        └───────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────────────┐
        │                       │                               │
        ▼                       ▼                               ▼
┌───────────────┐       ┌───────────────┐             ┌───────────────┐
│   Attempt 0   │       │   Attempt 1   │             │   Attempt 2   │
│   Strategy:   │       │   Strategy:   │             │   Strategy:   │
│   "default"   │       │   "geometry   │             │   "materials  │
│               │       │    first"     │             │    focus"     │
│   Qwen3-30B   │       │   Gemini Pro  │             │   Qwen3-30B   │
└───────┬───────┘       └───────┬───────┘             └───────┬───────┘
        │                       │                             │
        ▼                       ▼                             ▼
┌───────────────┐       ┌───────────────┐             ┌───────────────┐
│ Iter 0: 0.35  │       │ Iter 0: 0.40  │             │ Iter 0: 0.32  │
│ Iter 1: 0.52  │       │ Iter 1: 0.55  │             │ Iter 1: 0.48  │
│ Iter 2: 0.68  │       │ Iter 2: 0.72  │             │ Iter 2: 0.61  │
│ Iter 3: 0.78  │       │ Iter 3: 0.81  │             │ Iter 3: 0.73  │
│ Iter 4: 0.82  │       │ Iter 4: 0.88  │◀── BEST    │ Iter 4: 0.79  │
└───────────────┘       └───────────────┘             └───────────────┘
        │                       │                             │
        └───────────────────────┼─────────────────────────────┘
                                ▼
                    ┌───────────────────────┐
                    │   BEST: Attempt 1     │
                    │   Score: 0.88         │
                    │   Model: Gemini Pro   │
                    └───────────────────────┘
```

---

## 5. Research & Solutions

### 5.1 Summary Table

| Capability | Recommended Solution | Alternative | Notes |
|------------|---------------------|-------------|-------|
| **State Management** | LangGraph Checkpointer | Custom JSON | LangGraph provides SQLite, Postgres backends |
| **Orchestration** | LangGraph StateGraph | AsyncIO + Queues | Native support for parallel nodes |
| **Memory Tiers** | Custom hierarchy + LangGraph | MemGPT | Start simple, evolve |
| **Parallel Workers** | ProcessPoolExecutor | Ray | Local first, Ray for distributed |
| **Artifact Storage** | Filesystem + JSON | SQLite | Keep simple |
| **VLM Backend** | Qwen3-VL + Gemini fallback | Claude | Already implemented |
| **Blender Bridge** | Current addon.py | GenesisCore | Abstract interface for swap |

### 5.2 LangGraph Integration Plan

LangGraph is the recommended framework because:

1. **Checkpointing**: Built-in state persistence with SQLite/Postgres
2. **StateGraph**: Clean way to define agent workflows
3. **Parallel Execution**: Native `Send` for parallel nodes
4. **Interrupts**: Can pause and resume at any point
5. **Subgraphs**: Nested workflows (Coordinator → Attempt → VIGA)

**Migration Path:**
```
Phase 1: Wrap VIGA loop in LangGraph StateGraph
Phase 2: Add checkpointer for persistence
Phase 3: Implement Coordinator as parent graph
Phase 4: Add parallel attempt execution via Send
```

### 5.3 Memory Architecture Decision

**Chosen Approach: Tiered Memory with LangGraph Persistence**

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph
from typing import TypedDict, List, Optional

class GlobalState(TypedDict):
    """Persistent across all runs"""
    default_config: Dict
    learned_patterns: List[str]  # Future

class RunState(TypedDict):
    """Per-run state"""
    run_id: str
    task: str
    baseline_id: str
    attempts: List[AttemptState]
    best_attempt_id: Optional[str]
    status: str

class AttemptState(TypedDict):
    """Per-attempt state"""
    attempt_id: str
    strategy: str
    worker_id: int
    iterations: List[IterationState]
    final_score: float
    status: str

class IterationState(TypedDict):
    """Per-iteration state (VIGA context)"""
    iteration_id: int
    plan: str
    code: str
    execution_result: str
    visual_feedback: str
    score: float
    retry_count: int
```

---

## 6. Implementation Priorities

### Phase 0: Foundation (Week 1)
| Priority | Task | Deliverable |
|----------|------|-------------|
| P0 | Define state schemas | `state_manager/schemas.py` |
| P0 | Implement LangGraph VIGA graph | `agents/viga_graph.py` |
| P0 | Add SqliteSaver checkpointing | `state_manager/persistence.py` |
| P0 | Implement baseline reset | `runtime/baselines.py` |

### Phase 1: Coordinator (Week 2)
| Priority | Task | Deliverable |
|----------|------|-------------|
| P0 | Implement AttemptCoordinator | `agents/coordinator.py` |
| P0 | Sequential attempt execution | Integration test |
| P1 | Artifact folder creation | `runs/` structure |
| P1 | Score collection and selection | Best-of-N |

### Phase 2: Parallel Execution (Week 3)
| Priority | Task | Deliverable |
|----------|------|-------------|
| P1 | Worker pool implementation | `runtime/workers.py` |
| P1 | Multi-Blender port management | Port allocation |
| P1 | Parallel attempt execution | N workers |

### Phase 3: Polish (Week 4)
| Priority | Task | Deliverable |
|----------|------|-------------|
| P1 | Structured verifier output | Schema enforcement |
| P1 | Fast-fix retry loop | Error recovery |
| P2 | History compression | Token management |
| P2 | Strategy variation | Different prompts |

---

## 7. Open Questions

### 7.1 Architectural Decisions Needed

| Question | Options | Current Leaning |
|----------|---------|-----------------|
| Keep legacy D5 orchestrator? | Merge, Replace, Keep Both | Replace with LangGraph |
| Local vs distributed workers? | Local ProcessPool, Ray, Remote | Local first |
| Blender startup management? | Manual, Script, Container | Script (`launch_blender.ps1`) |
| Memory compression approach? | Summarize, Truncate, Embedding | Summarize with LLM |

### 7.2 Technical Unknowns

1. **LangGraph Send + Checkpointing**: Does parallel `Send` work correctly with checkpointing?
2. **Blender stability**: Can Blender handle 3-4 instances on one machine?
3. **VLM latency**: What's the impact of VLM calls on iteration speed?
4. **Token limits**: How many iterations before context window explodes?

### 7.3 Future Capabilities (Not in Scope)

- [ ] Remote worker deployment (cloud GPUs)
- [ ] Web UI for monitoring runs
- [ ] Cross-session learning (RL from feedback)
- [ ] Blueprint-driven geometric constraints
- [ ] Asset library integration (beyond PolyHaven)

---

## Appendix A: Additional Capabilities Discovered in Code

### A.1 Game Asset Pipeline (`game_asset_agent.py`)

A complete standalone pipeline for converting Blender meshes to game-ready assets:

| Stage | Description | Status |
|-------|-------------|--------|
| 1. Import Mesh | OBJ/FBX/BLEND import | ✅ |
| 2. Topology Cleanup | Remove doubles, dissolve n-gons | ✅ |
| 3. UV Unwrapping | Smart UV Project + pack | ✅ |
| 4. PBR Materials | Profile-based material gen | ✅ |
| 5. Normal Baking | High→Low poly (stub) | ⚠️ Stub only |
| 6. LOD Generation | Decimate-based LOD0-LOD3 | ✅ |
| 7. FBX Export | Game engine compatible | ✅ |
| 8. Validation | Quality metrics | ✅ |

**Integration Opportunity:** This can be the "post-processing" stage after VIGA creates the base asset.

### A.2 GLM-4.5V Vision (`glm_vision.py`)

Alternative vision backend using Z.AI's GLM-4.5V model:

| Feature | Details |
|---------|---------|
| Model | GLM-4.5V (106B params, 12B active) |
| Context | 64K tokens |
| Endpoint | `api.z.ai/api/coding/paas/v4` |
| Auth | Bearer token via `ZAI_API_KEY` |
| Thinking Mode | Deep reasoning support |

**Use Case:** Alternative to Qwen3-VL for verification, especially for complex spatial reasoning.

### A.3 GPU Configuration (`gpu_config.py`)

Render optimization presets for high-end GPUs:

| GPU | VRAM | Tile Size | Samples (Preview/Production/Final) |
|-----|------|-----------|-----------------------------------|
| RTX 3090 | 24GB | 256 | 64 / 128 / 256 |
| RTX 5090 | 32GB | 512 | 128 / 256 / 512 |

**Integration Opportunity:** Apply optimal GPU settings before rendering diagnostic views.

### A.4 Game Asset Profiles (`game_asset_config.py`)

Pre-configured profiles for different game engines:

- **War Thunder**: Military vehicle constraints
- **World of Warships**: Naval vessel requirements
- **Unity Standard**: General game assets
- **Unreal Standard**: UE-compatible settings

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **VIGA** | Vision-as-Inverse-Graphics Analysis-by-Synthesis |
| **Attempt** | One complete run from baseline with a strategy |
| **Iteration** | One Generator→Execute→Verify cycle within an attempt |
| **Baseline** | The starting .blend file for all attempts |
| **Coordinator** | Outer loop managing N attempts |
| **Worker** | Process running one attempt with one Blender |
| **Checkpoint** | Saved state that can be resumed |

## Appendix C: Reference Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Architecture | `docs/architecture.md` | Component overview |
| VIGA Algorithm | `docs/viga/viga_algorithm.md` | Inner loop spec |
| Attempt Coordinator | `docs/plans/attempt_coordinator.md` | Outer loop spec |
| Parallelization | `docs/plans/parallelization_workers.md` | Worker design |
| Scoring | `docs/plans/scoring_and_selection.md` | Best selection |
| Artifacts | `docs/plans/artifacts_and_reproducibility.md` | Output format |
| Baselines | `docs/plans/blender_reset_and_baselines.md` | Scene reset |
| Self-Correction | `docs/plans/self_correction_loop.md` | Fast retry |

---

*Document generated by analyzing existing plans, source code, and researching framework solutions.*
