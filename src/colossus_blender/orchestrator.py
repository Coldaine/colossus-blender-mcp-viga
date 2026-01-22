"""
ColossusD5 Multi-Agent Orchestrator for Blender MCP
Based on Research Agent D5 decomposition pattern with vision feedback loops

Architecture:
    User Intent → Planner → Designer → Executor → Evaluator → Refiner
                                           ↓            ↓
                                       Screenshot   Quality Score
                                                       ↓
                                               Loop or Exit
"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class AgentRole(Enum):
    """Agent roles in the D5 decomposition pattern"""
    PLANNER = "planner"
    DESIGNER = "designer"
    EXECUTOR = "executor"
    EVALUATOR = "evaluator"
    REFINER = "refiner"


@dataclass
class WorkflowState:
    """State object passed between agents"""
    user_intent: str
    current_iteration: int = 0
    max_iterations: int = 3
    satisfaction_threshold: float = 0.75

    # Planning output
    subtasks: List[Dict[str, Any]] = field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)

    # Design output
    blender_code: str = ""
    code_metadata: Dict[str, Any] = field(default_factory=dict)

    # Execution output
    execution_result: Dict[str, Any] = field(default_factory=dict)
    screenshot_base64: Optional[str] = None

    # Evaluation output
    quality_score: float = 0.0
    visual_feedback: Dict[str, Any] = field(default_factory=dict)
    is_satisfied: bool = False

    # Refinement output
    refinement_suggestions: List[str] = field(default_factory=list)

    # History tracking
    iteration_history: List[Dict[str, Any]] = field(default_factory=list)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)


class PlannerAgent:
    """
    Decomposes user intent into executable subtasks with dependency graphs
    """

    def __init__(self, llm_client):
        self.llm = llm_client
        self.role = AgentRole.PLANNER

    async def plan(self, state: WorkflowState) -> WorkflowState:
        """Decompose user intent into subtasks"""

        prompt = f"""You are a 3D scene planning expert. Break down the user's intent into concrete, executable subtasks for Blender.

User Intent: {state.user_intent}

Analyze the intent and create:
1. A list of subtasks (each should be a single Blender operation)
2. Dependency relationships between tasks

Output JSON format:
{{
    "subtasks": [
        {{"id": "task_1", "description": "Clean existing scene", "dependencies": []}},
        {{"id": "task_2", "description": "Set up camera at (7, -7, 5)", "dependencies": ["task_1"]}},
        {{"id": "task_3", "description": "Add main objects", "dependencies": ["task_1"]}},
        ...
    ],
    "complexity_estimate": "simple|moderate|complex",
    "estimated_iterations": 2
}}

Focus on:
- Clear, atomic tasks
- Proper ordering (dependencies)
- Realistic scope (achievable in Blender)
"""

        response = await self.llm.ainvoke([
            {"role": "system", "content": "You are an expert 3D scene planner."},
            {"role": "user", "content": prompt}
        ])

        try:
            plan_data = json.loads(response.content)
            state.subtasks = plan_data["subtasks"]

            # Build dependency graph
            state.dependency_graph = {
                task["id"]: task.get("dependencies", [])
                for task in state.subtasks
            }

            # Adjust max iterations based on complexity
            if plan_data.get("estimated_iterations"):
                state.max_iterations = min(plan_data["estimated_iterations"], 5)

        except json.JSONDecodeError as e:
            # Fallback: create simple single-task plan
            state.subtasks = [{
                "id": "task_1",
                "description": state.user_intent,
                "dependencies": []
            }]
            state.dependency_graph = {"task_1": []}

        return state


class DesignerAgent:
    """
    Generates high-quality Blender Python code with GPU optimization hints
    """

    def __init__(self, llm_client, system_prompt: str, gpu_mode: str = "3090"):
        self.llm = llm_client
        self.role = AgentRole.DESIGNER
        self.system_prompt = system_prompt
        self.gpu_mode = gpu_mode

    async def design(self, state: WorkflowState) -> WorkflowState:
        """Generate Blender Python code"""

        # Build context from previous iterations
        context = ""
        if state.iteration_history:
            last_iter = state.iteration_history[-1]
            context = f"""
Previous iteration feedback:
- Quality score: {last_iter.get('quality_score', 0):.2f}
- Issues: {', '.join(last_iter.get('issues', []))}
- Suggestions: {', '.join(last_iter.get('suggestions', []))}
"""

        # Build task list
        task_descriptions = "\n".join([
            f"- {task['description']}" for task in state.subtasks
        ])

        prompt = f"""Generate Blender Python code to accomplish the following:

User Intent: {state.user_intent}

Tasks to implement:
{task_descriptions}

GPU Mode: {self.gpu_mode}

{context}

Requirements:
1. Use the code templates from the system prompt
2. Configure GPU settings for {self.gpu_mode}
3. Return JSON metadata for MCP communication
4. Include error handling
5. Optimize for vision-based evaluation (good camera angles, lighting)

Generate complete, executable Python code wrapped in ```python blocks.
"""

        response = await self.llm.ainvoke([
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ])

        # Extract code from response
        code_content = response.content
        if "```python" in code_content:
            code_blocks = code_content.split("```python")[1:]
            state.blender_code = code_blocks[0].split("```")[0].strip()
        else:
            state.blender_code = code_content

        state.code_metadata = {
            "gpu_mode": self.gpu_mode,
            "task_count": len(state.subtasks),
            "iteration": state.current_iteration
        }

        return state


class ExecutorAgent:
    """
    Runs code via Blender MCP with error handling + metadata capture
    """

    def __init__(self, mcp_client):
        self.mcp = mcp_client
        self.role = AgentRole.EXECUTOR

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute Blender code via MCP"""

        try:
            # Execute code in Blender
            exec_result = await self.mcp.execute_code(state.blender_code)

            state.execution_result = {
                "status": exec_result.get("status", "unknown"),
                "output": exec_result.get("output", ""),
                "errors": exec_result.get("errors", [])
            }

            # Capture screenshot if execution succeeded
            if exec_result.get("status") == "success":
                screenshot_result = await self.mcp.get_viewport_screenshot(max_size=1024)
                state.screenshot_base64 = screenshot_result.get("image_data")

        except Exception as e:
            state.execution_result = {
                "status": "error",
                "output": "",
                "errors": [str(e)]
            }

        return state


class EvaluatorAgent:
    """
    Analyzes viewport screenshots via local Qwen2.5-VL-72B vision model for quality scoring (0-1.0)

    Uses local Qwen2.5-VL-72B:
    - 72B parameters with INT4 quantization
    - Multi-image comparison capability
    - Optimized for battleship geometric analysis
    - Unlimited iterations (no API costs)
    - Hybrid VLM + OpenCV measurements
    """

    def __init__(self, vision_client):
        self.vision_client = vision_client
        self.role = AgentRole.EVALUATOR

    async def evaluate(self, state: WorkflowState) -> WorkflowState:
        """Analyze screenshot and rate quality using local Qwen2.5-VL"""

        if not state.screenshot_base64:
            state.quality_score = 0.0
            state.visual_feedback = {
                "error": "No screenshot available for evaluation"
            }
            return state

        try:
            # Get previous feedback if available
            previous_feedback = None
            if state.iteration_history:
                previous_feedback = state.iteration_history[-1]

            # Use local Qwen2.5-VL to analyze the scene
            eval_data = await self.vision_client.analyze_scene(
                screenshot_base64=state.screenshot_base64,
                user_intent=state.user_intent,
                iteration=state.current_iteration,
                max_iterations=state.max_iterations,
                previous_feedback=previous_feedback
            )

            state.quality_score = eval_data.get("overall_score", 0.0)
            state.visual_feedback = eval_data
            state.is_satisfied = (
                state.quality_score >= state.satisfaction_threshold or
                eval_data.get("is_satisfactory", False)
            )

            # Log hybrid analysis if available
            if "hybrid_analysis" in eval_data:
                print(f"[Hybrid Analysis] VLM + OpenCV measurements included")

        except Exception as e:
            state.quality_score = 0.5  # Neutral fallback
            state.visual_feedback = {
                "error": f"Vision model evaluation failed: {str(e)}",
                "issues": ["Could not evaluate screenshot"],
                "specific_suggestions": []
            }

        return state


class RefinerAgent:
    """
    Generates targeted improvement code based on vision feedback
    """

    def __init__(self, llm_client, system_prompt: str):
        self.llm = llm_client
        self.role = AgentRole.REFINER
        self.system_prompt = system_prompt

    async def refine(self, state: WorkflowState) -> WorkflowState:
        """Generate refinement code based on feedback"""

        if state.is_satisfied:
            # No refinement needed
            state.refinement_suggestions = []
            return state

        issues = state.visual_feedback.get("issues", [])
        suggestions = state.visual_feedback.get("specific_suggestions", [])

        prompt = f"""The current Blender scene needs improvement.

Original Goal: {state.user_intent}
Quality Score: {state.quality_score:.2f} (threshold: {state.satisfaction_threshold})

Issues Identified:
{chr(10).join(f"- {issue}" for issue in issues)}

Specific Suggestions:
{chr(10).join(f"- {suggestion}" for suggestion in suggestions)}

Generate Python code that applies ONLY these specific improvements.
Do NOT recreate the entire scene - just modify existing objects.

Focus on:
1. Adjusting lighting (energy, color, position)
2. Moving camera (location, rotation)
3. Tweaking materials (color, roughness, metallic)
4. Small geometry adjustments

Provide concise, targeted code that fixes the issues.
"""

        response = await self.llm.ainvoke([
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ])

        # Extract refinement code
        code_content = response.content
        if "```python" in code_content:
            code_blocks = code_content.split("```python")[1:]
            refinement_code = code_blocks[0].split("```")[0].strip()
        else:
            refinement_code = code_content

        # Update state with refinement code (will be used in next iteration)
        state.blender_code = refinement_code
        state.refinement_suggestions = suggestions

        return state


class ColossusD5Orchestrator:
    """
    Main orchestrator that coordinates all agents in the D5 workflow
    """

    def __init__(
        self,
        claude_llm,
        vision_llm,
        blender_mcp_client,
        system_prompt: str,
        gpu_mode: str = "3090"
    ):
        self.planner = PlannerAgent(claude_llm)
        self.designer = DesignerAgent(claude_llm, system_prompt, gpu_mode)
        self.executor = ExecutorAgent(blender_mcp_client)
        self.evaluator = EvaluatorAgent(vision_llm)
        self.refiner = RefinerAgent(claude_llm, system_prompt)

        self.gpu_mode = gpu_mode

    async def run(self, state: WorkflowState) -> WorkflowState:
        """Execute the complete D5 workflow"""

        # Phase 1: Planning (once at the start)
        print(f"[PLANNER] Analyzing user intent...")
        state = await self.planner.plan(state)
        print(f"[PLANNER] Created {len(state.subtasks)} subtasks")

        # Phase 2-6: Design → Execute → Evaluate → Refine (iterative loop)
        for iteration in range(state.max_iterations):
            state.current_iteration = iteration
            print(f"\n=== Iteration {iteration + 1}/{state.max_iterations} ===")

            # Design
            print(f"[DESIGNER] Generating Blender code...")
            state = await self.designer.design(state)
            print(f"[DESIGNER] Code generated ({len(state.blender_code)} chars)")

            # Execute
            print(f"[EXECUTOR] Running code in Blender...")
            state = await self.executor.execute(state)

            if state.execution_result.get("status") != "success":
                print(f"[EXECUTOR] Execution failed: {state.execution_result.get('errors')}")
                # Save to history and try refinement
                state.iteration_history.append({
                    "iteration": iteration,
                    "execution_failed": True,
                    "errors": state.execution_result.get("errors", [])
                })
                continue

            print(f"[EXECUTOR] Execution succeeded, screenshot captured")

            # Evaluate
            print(f"[EVALUATOR] Analyzing screenshot...")
            state = await self.evaluator.evaluate(state)
            print(f"[EVALUATOR] Quality score: {state.quality_score:.2%}")

            # Save iteration to history
            state.iteration_history.append({
                "iteration": iteration,
                "quality_score": state.quality_score,
                "issues": state.visual_feedback.get("issues", []),
                "suggestions": state.visual_feedback.get("specific_suggestions", []),
                "is_satisfied": state.is_satisfied
            })

            # Check if satisfied
            if state.is_satisfied:
                print(f"[ORCHESTRATOR] Quality threshold met! Stopping.")
                break

            # Refine for next iteration
            if iteration < state.max_iterations - 1:
                print(f"[REFINER] Generating improvements...")
                state = await self.refiner.refine(state)
                print(f"[REFINER] {len(state.refinement_suggestions)} suggestions applied")

        # Final summary
        print(f"\n=== Workflow Complete ===")
        print(f"Final Quality: {state.quality_score:.1%}")
        print(f"Iterations Used: {state.current_iteration + 1}/{state.max_iterations}")
        print(f"Satisfied: {state.is_satisfied}")

        return state


# Utility function for quick testing
async def create_scene_iteratively(
    user_intent: str,
    claude_llm,
    vision_llm,
    mcp_client,
    system_prompt: str,
    gpu_mode: str = "3090",
    max_iterations: int = 3,
    satisfaction_threshold: float = 0.75
):
    """Convenience function for creating scenes with vision feedback"""

    orchestrator = ColossusD5Orchestrator(
        claude_llm=claude_llm,
        vision_llm=vision_llm,
        blender_mcp_client=mcp_client,
        system_prompt=system_prompt,
        gpu_mode=gpu_mode
    )

    state = WorkflowState(
        user_intent=user_intent,
        max_iterations=max_iterations,
        satisfaction_threshold=satisfaction_threshold
    )

    final_state = await orchestrator.run(state)

    return final_state
