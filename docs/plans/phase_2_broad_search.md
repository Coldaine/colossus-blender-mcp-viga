# Phase II: Broad Search (Parallel Attempts)

**Goal:** Run N parallel attempts from the same baseline, each with the Phase I inner loop, and select the best result.

**Prerequisites:** Phase I complete and validated (single-attempt loop works reliably).

**Cross-references:**
- [MASTER_REQUIREMENTS.md](../MASTER_REQUIREMENTS.md) — full requirements
- [phase_1_mvp_inner_loop.md](./phase_1_mvp_inner_loop.md) — Phase I (inner loop)
- [attempt_coordinator.md](./attempt_coordinator.md) — Coordinator design
- [parallelization_workers.md](./parallelization_workers.md) — Worker pool design
- [scoring_and_selection.md](./scoring_and_selection.md) — Selection criteria

---

## 1. Scope

### In Scope (Phase II)
- Attempt Coordinator that spawns N attempts
- Worker pool with one Blender instance per worker
- Baseline isolation (each attempt starts from same state)
- Score collection and best-of-N selection
- Strategy variation (optional: different prompts per attempt)
- Run-level artifact aggregation

### Out of Scope (Phase II)
- Distributed workers across machines
- Dynamic attempt spawning (beam search)
- Cross-attempt learning
- Advanced model routing per attempt

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RUN SETUP                                       │
│  - Create run folder                                                        │
│  - Prepare baseline .blend                                                  │
│  - Initialize Coordinator state                                             │
│  - Spawn worker pool (N Blender instances on ports 9876-987X)               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ATTEMPT COORDINATOR                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        DISPATCH ATTEMPTS                             │   │
│  │  For each attempt_id in 0..N-1:                                      │   │
│  │    - Assign to worker                                                │   │
│  │    - Apply strategy variant (optional)                               │   │
│  │    - Start Phase I inner loop                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         WORKER POOL                                  │   │
│  │                                                                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │ Worker 0 │  │ Worker 1 │  │ Worker 2 │  │ Worker N │            │   │
│  │  │ :9876    │  │ :9877    │  │ :9878    │  │ :987X    │            │   │
│  │  │          │  │          │  │          │  │          │            │   │
│  │  │ Phase I  │  │ Phase I  │  │ Phase I  │  │ Phase I  │            │   │
│  │  │ Loop     │  │ Loop     │  │ Loop     │  │ Loop     │            │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │   │
│  │       │             │             │             │                   │   │
│  │       ▼             ▼             ▼             ▼                   │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │                    RESULTS COLLECTION                        │  │   │
│  │  │  Collect: final_score, status, attempt_id, artifact_path     │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         SELECTION                                    │   │
│  │  - Rank attempts by final_score                                      │   │
│  │  - Select best (highest score)                                       │   │
│  │  - Record selection rationale                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FINALIZATION                                    │
│  - Copy best attempt's final.blend to run root                              │
│  - Write best_attempt.json                                                  │
│  - Write run summary.json                                                   │
│  - Shutdown worker pool                                                     │
│  - Optionally run GameAssetAgent on winner                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. State Schema

### 3.1 Coordinator State (Run Level)

```python
class CoordinatorState(TypedDict):
    # Identity
    run_id: str
    
    # Task (shared by all attempts)
    task_description: str
    reference_images: List[str]
    baseline_path: str
    
    # Workers
    worker_count: int
    worker_ports: List[int]  # [9876, 9877, ...]
    
    # Attempts
    attempt_count: int
    attempts: List[AttemptResult]
    pending_attempts: List[str]  # attempt_ids not yet started
    running_attempts: List[str]  # attempt_ids in progress
    completed_attempts: List[str]  # attempt_ids finished
    
    # Selection
    best_attempt_id: Optional[str]
    best_score: float
    
    # Control
    status: Literal["initializing", "running", "selecting", "finalizing", "completed", "failed"]
    
    # Config
    config: Dict[str, Any]
```

### 3.2 Attempt Result

```python
class AttemptResult(TypedDict):
    attempt_id: str
    worker_id: int
    strategy: str  # name of strategy variant
    
    # Outcome
    final_score: float
    iterations_run: int
    status: Literal["converged", "budget_exhausted", "stagnant", "failed"]
    
    # Paths
    artifact_path: str  # runs/{run_id}/attempt-{id}/
    final_blend_path: str
    
    # Timing
    start_time: str
    end_time: str
    duration_seconds: float
```

---

## 4. Worker Pool Design

### 4.1 Worker Lifecycle

```python
class Worker:
    def __init__(self, worker_id: int, port: int):
        self.worker_id = worker_id
        self.port = port
        self.blender_process: Optional[subprocess.Popen] = None
        self.mcp_client: Optional[BlenderMCPClient] = None
        self.current_attempt: Optional[str] = None
        self.status: Literal["idle", "busy", "failed"] = "idle"
    
    async def start_blender(self):
        """Launch Blender with MCP addon on assigned port."""
        self.blender_process = subprocess.Popen([
            "blender", "--background", "--python", "start_mcp_server.py",
            "--", f"--port={self.port}"
        ])
        await self._wait_for_mcp_ready()
        self.mcp_client = BlenderMCPClient(port=self.port)
    
    async def run_attempt(self, attempt_config: AttemptConfig) -> AttemptResult:
        """Run Phase I loop for one attempt."""
        self.status = "busy"
        self.current_attempt = attempt_config.attempt_id
        
        # Reset to baseline
        await self.mcp_client.reset_to_baseline(attempt_config.baseline_path)
        
        # Run Phase I graph
        result = await run_phase1_loop(
            mcp_client=self.mcp_client,
            attempt_config=attempt_config,
        )
        
        self.status = "idle"
        self.current_attempt = None
        return result
    
    async def shutdown(self):
        """Stop Blender process."""
        if self.blender_process:
            self.blender_process.terminate()
            await asyncio.wait_for(self.blender_process.wait(), timeout=10)
```

### 4.2 Pool Manager

```python
class WorkerPool:
    def __init__(self, worker_count: int, base_port: int = 9876):
        self.workers = [
            Worker(worker_id=i, port=base_port + i)
            for i in range(worker_count)
        ]
    
    async def start_all(self):
        """Start all Blender instances in parallel."""
        await asyncio.gather(*[w.start_blender() for w in self.workers])
    
    async def run_attempts(self, attempt_configs: List[AttemptConfig]) -> List[AttemptResult]:
        """Run all attempts, dispatching to workers as they become available."""
        results = []
        pending = list(attempt_configs)
        
        async def worker_loop(worker: Worker):
            while pending:
                config = pending.pop(0)
                result = await worker.run_attempt(config)
                results.append(result)
        
        await asyncio.gather(*[worker_loop(w) for w in self.workers])
        return results
    
    async def shutdown_all(self):
        """Stop all Blender instances."""
        await asyncio.gather(*[w.shutdown() for w in self.workers])
```

---

## 5. Strategy Variants

Optional: different attempts can use different strategies to increase diversity.

```python
STRATEGIES = {
    "default": {
        "system_prompt_addon": "",
        "focus": "balanced",
    },
    "geometry_first": {
        "system_prompt_addon": "Focus on getting the geometry right before materials/lighting.",
        "focus": "geometry",
    },
    "proportions_first": {
        "system_prompt_addon": "Prioritize correct proportions and scale above all else.",
        "focus": "proportions",
    },
    "conservative": {
        "system_prompt_addon": "Make small, incremental changes. Avoid large rewrites.",
        "focus": "stability",
    },
    "aggressive": {
        "system_prompt_addon": "Don't be afraid to make significant changes if needed.",
        "focus": "speed",
    },
}

def assign_strategies(attempt_count: int) -> List[str]:
    """Assign strategies to attempts (round-robin or weighted)."""
    strategy_names = list(STRATEGIES.keys())
    return [strategy_names[i % len(strategy_names)] for i in range(attempt_count)]
```

---

## 6. Selection Criteria

```python
def select_best_attempt(results: List[AttemptResult]) -> AttemptResult:
    """Select the best attempt based on scoring criteria."""
    
    # Filter to successful attempts only
    valid = [r for r in results if r["status"] in ("converged", "budget_exhausted", "stagnant")]
    
    if not valid:
        raise RuntimeError("No valid attempts completed")
    
    # Primary sort: final_score (descending)
    # Secondary sort: iterations_run (ascending, prefer faster)
    # Tertiary sort: status (prefer "converged")
    
    def sort_key(r: AttemptResult):
        status_rank = {"converged": 0, "budget_exhausted": 1, "stagnant": 2}
        return (-r["final_score"], r["iterations_run"], status_rank.get(r["status"], 3))
    
    sorted_results = sorted(valid, key=sort_key)
    return sorted_results[0]
```

---

## 7. Artifact Structure

```
runs/
  {timestamp}_{task_slug}/
    run.json                      # Run config, attempt count, worker count
    baseline.blend                # Starting state (shared)
    
    attempt-000/
      config.json                 # Strategy, worker assignment
      iterations/
        iter-000/
          ...
        iter-001/
          ...
      final_score.json
      final.blend
    
    attempt-001/
      ...
    
    attempt-002/
      ...
    
    best_attempt.json             # Which attempt won, why
    final.blend                   # Copy of winner's final.blend
    summary.json                  # Run summary with all attempt scores
```

---

## 8. LangGraph Implementation

```python
from langgraph.graph import StateGraph, START, END

def initialize_node(state: CoordinatorState) -> CoordinatorState:
    """Set up run folder, prepare baseline, start worker pool."""
    run_folder = create_run_folder(state["run_id"], state["task_description"])
    copy_baseline(state["baseline_path"], run_folder)
    
    attempt_ids = [f"attempt-{i:03d}" for i in range(state["attempt_count"])]
    strategies = assign_strategies(state["attempt_count"])
    
    return {
        **state,
        "pending_attempts": attempt_ids,
        "running_attempts": [],
        "completed_attempts": [],
        "attempts": [],
        "status": "running",
    }

def dispatch_node(state: CoordinatorState) -> CoordinatorState:
    """Dispatch attempts to workers and wait for all to complete."""
    configs = [
        AttemptConfig(
            attempt_id=aid,
            strategy=STRATEGIES[assign_strategies(state["attempt_count"])[i]],
            baseline_path=state["baseline_path"],
            task_description=state["task_description"],
            reference_images=state["reference_images"],
            config=state["config"],
        )
        for i, aid in enumerate(state["pending_attempts"])
    ]
    
    pool = WorkerPool(state["worker_count"])
    results = asyncio.run(pool.run_attempts(configs))
    
    return {
        **state,
        "attempts": results,
        "pending_attempts": [],
        "running_attempts": [],
        "completed_attempts": [r["attempt_id"] for r in results],
        "status": "selecting",
    }

def select_node(state: CoordinatorState) -> CoordinatorState:
    """Select best attempt."""
    best = select_best_attempt(state["attempts"])
    return {
        **state,
        "best_attempt_id": best["attempt_id"],
        "best_score": best["final_score"],
        "status": "finalizing",
    }

def finalize_node(state: CoordinatorState) -> CoordinatorState:
    """Copy winner, write summaries, shutdown."""
    copy_winner_to_run_root(state["run_id"], state["best_attempt_id"])
    write_best_attempt_json(state)
    write_run_summary(state)
    return {
        **state,
        "status": "completed",
    }

# Build graph
builder = StateGraph(CoordinatorState)
builder.add_node("initialize", initialize_node)
builder.add_node("dispatch", dispatch_node)
builder.add_node("select", select_node)
builder.add_node("finalize", finalize_node)

builder.add_edge(START, "initialize")
builder.add_edge("initialize", "dispatch")
builder.add_edge("dispatch", "select")
builder.add_edge("select", "finalize")
builder.add_edge("finalize", END)

coordinator_graph = builder.compile(checkpointer=checkpointer)
```

---

## 9. Test Plan (TDD)

### 9.1 Unit Tests

| Test | What it validates |
|------|-------------------|
| `test_coordinator_state_schema` | State serializes correctly |
| `test_strategy_assignment` | Strategies assigned round-robin |
| `test_selection_criteria` | Best attempt selected correctly |
| `test_worker_port_assignment` | Ports assigned without collision |

### 9.2 Integration Tests

| Test | What it validates |
|------|-------------------|
| `test_worker_start_blender` | Can launch Blender with MCP |
| `test_worker_reset_baseline` | Worker can reset to baseline |
| `test_worker_run_single_attempt` | Worker runs Phase I loop |
| `test_pool_parallel_execution` | Multiple workers run in parallel |
| `test_results_collection` | Results collected from all workers |

### 9.3 End-to-End Tests

| Test | What it validates |
|------|-------------------|
| `test_3_attempts_selection` | 3 attempts, best selected |
| `test_all_attempts_fail` | Graceful handling when all fail |
| `test_mixed_strategies` | Different strategies produce different results |
| `test_artifact_aggregation` | All attempt artifacts + summary written |
| `test_checkpoint_resume` | Can resume coordinator mid-run |

---

## 10. Implementation Order

### Week 5: Worker Pool (after Phase I complete)
1. [ ] Implement Worker class with Blender lifecycle
2. [ ] Implement WorkerPool with parallel dispatch
3. [ ] Create `start_mcp_server.py` script for Blender
4. [ ] Write integration tests for worker operations
5. [ ] Test with 2 workers, simple task

### Week 6: Coordinator
1. [ ] Implement CoordinatorState schema
2. [ ] Implement initialize/dispatch/select/finalize nodes
3. [ ] Implement strategy variants
4. [ ] Implement selection criteria
5. [ ] Wire up LangGraph with checkpointing

### Week 7: Integration
1. [ ] Run 3-attempt test on real hull task
2. [ ] Validate artifact structure
3. [ ] Debug worker failures / cleanup
4. [ ] Add proper logging throughout
5. [ ] Performance profiling

### Week 8: Polish
1. [ ] Add worker health monitoring
2. [ ] Add timeout handling
3. [ ] Add graceful shutdown on Ctrl+C
4. [ ] Documentation
5. [ ] Demo run with N=5 attempts

---

## 11. Success Metrics

| Metric | Target |
|--------|--------|
| All attempts complete | >90% (tolerate 1 failure in 10) |
| Best attempt selected correctly | 100% |
| Parallel speedup | Near-linear up to worker count |
| Artifact logging complete | 100% |
| Resume from checkpoint | Works |

---

## 12. Future Enhancements (Phase III+)

- **Beam search:** Dynamically spawn more attempts if scores cluster low
- **Cross-attempt learning:** Share insights between attempts
- **Distributed workers:** Run workers on remote machines
- **GPU scheduling:** Route vision-heavy evaluation to GPU workers
- **Adaptive strategies:** Learn which strategies work best for which tasks

---

**Previous:** [Phase I: MVP Inner Loop](./phase_1_mvp_inner_loop.md)
**Next:** Phase III (future)
