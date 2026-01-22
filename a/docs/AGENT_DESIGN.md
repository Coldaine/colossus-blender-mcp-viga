# Colossus Agent Design: Generator and Verifier

The VIGA framework decentralizes the 3D creation process into two specialized roles: the **Generator** and the **Verifier**. This separation of concerns allows for rigorous "Analysis-by-Synthesis," where the system continuously compares its mental model against the actual rendered output.

## 1. The Generator (Synthesis)

The Generator is responsible for translating high-level user intent and visual feedback into executable Blender Python code.

### Responsibilities
- **Planning**: Decomposing complex 3D scenes into logical steps (e.g., base geometry, refined modifiers, material assignment, lighting).
- **Code Synthesis**: Writing robust, error-tolerant Python scripts that utilize the `bpy` API.
- **Iterative Refinement**: Modifying previous code versions based on feedback from the Verifier.

### Technical Workflow
The Generator receives:
1.  The original task description.
2.  The current plan.
3.  The full execution history (code and internal logs).
4.  Feedback from the Verifier.

It outputs a standalone Python script designed to be run via the **Blender MCP Client**.

---

## 2. The Verifier (Analysis)

The Verifier acts as the "eyes" of the system. It does not write code but instead evaluates the state of the Blender environment using active exploration.

### Responsibilities
- **Active Exploration**: Controlling the Blender camera to find the best angle for inspection.
- **Visual Analysis**: Using the VLM (Qwen3-VL) to "see" the viewport screenshot.
- **Comparative Feedback**: Measuring the difference between the "as-is" state and the "to-be" objective.
- **Convergence Detection**: Signaling the system when the goal has been achieved.

### Technical Workflow
1.  **Viewpoint Initialization**: Framing the bounding box of all objects in the scene.
2.  **Screenshot Capture**: Requesting a 1024px render from the Blender viewport.
3.  **VLM Inference**: Processing the image to identify missing elements, lighting issues, or geometric inaccuracies.
4.  **Feedback Loop**: Providing structured text feedback (e.g., "The cube is missing a bevel, and the material is too reflective") to the Generator.

---

## 3. Communication Patterns

The two agents communicate through the **VIGA Memory** system. 

| Phase | Agent | Input | Output |
|---|---|---|---|
| **Synthesis** | Generator | Task + Feedback | Blender Code |
| **Execution** | Environment | Code | Log + Modified Scene |
| **Verification** | Verifier | Scene + Task | Structured Feedback |
| **Commit** | Memory | All above | Normalized Context |

## 4. Key Models (Jan 2026)

- **Generator Backbone**: Qwen3-VL-30B (Optimized for coding precision).
- **Verifier Backbone**: Qwen3-VL-30B (Native vision/interleaved token support).
- **Fallback**: Gemini 3 Pro (Used if local VRAM is constrained).

---
*Version: 0.1.0 | Date: January 2026*
