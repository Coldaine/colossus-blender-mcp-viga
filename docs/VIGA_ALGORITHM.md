# VIGA: Vision-as-Inverse-Graphics Analysis-by-Synthesis

The VIGA framework implements a closed-loop system where 3D scene creation is treated as a search problem in the synthesis space, guided by visual verification.

## Algorithm 1: VIGA Loop

The process follows four distinct phases per iteration:

### 1. Planning & Synthesis (Generator)
- **Input**: User task, execution history, and visual feedback from previous iterations.
- **Process**: The Generator (LLM) updates its high-level plan and synthesizes a new version of the Blender Python program ($P_t$).
- **Code**: `GeneratorAgent.generate_step()` in `src/colossus_blender/viga/agent.py`.

### 2. Environment Execution
- **Input**: Synthesized code $P_t$.
- **Process**: The code is sent to the **Blender MCP Client**. The client executes the script in the live Blender environment.
- **Output**: A modified scene and an execution log (success/error).

### 3. Active Exploration & Verification (Verifier)
- **Input**: The live Blender scene.
- **Process**:
    - **Step A**: The Verifier initializes a viewpoint that frames the current scene content.
    - **Step B**: The Verifier captures a high-resolution screenshot.
    - **Step C**: The Verifier (VLM) analyzes the image against the original task and the internal "mental model" of what the scene should look like.
- **Code**: `VerifierAgent.verify_step()`.

### 4. Memory Update
- **Input**: Plan, Code, Execution Log, and Visual Feedback.
- **Process**: The iteration results are stored in the memory window, providing context for the next generation step.

## Convergence
The loop terminates when:
1.  The Verifier identifies the objective as fully complete.
2.  The maximum number of iterations ($T_{max}$) is reached.

## Comparison with D5 Loop
| Feature | VIGA Loop | D5 Orchestrator |
|---|---|---|
| **Logic** | Analysis-by-Synthesis | Task Decomposition |
| **Vision** | Active Exploration (Viewpoint Control) | Passive Screenshot |
| **Feedback** | Direct Inverse-Graphics alignment | Multi-Score Quality Index |
| **Backbone** | Qwen3-VL (Interleaved Vision) | Claude 3.5 + Evaluator VLM |
