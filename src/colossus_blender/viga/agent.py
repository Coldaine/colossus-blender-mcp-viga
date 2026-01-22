"""
VIGA Agent Architecture
Implements the VIGA Analysis-by-Synthesis Loop (Algorithm 1) from arXiv:2601.11109v1
"""

from typing import Optional, Dict, Any, List
import asyncio
from .memory import VIGAMemory, IterationContext
from .skills import SkillLibrary
from ..mcp_client import BlenderMCPClient
from ..vision_utils import extract_code_from_response
from .modern_models import FoundationModel, get_model


class GeneratorAgent:
    def __init__(self, skills: SkillLibrary, model: FoundationModel):
        self.skills = skills
        self.model = model

    async def generate_step(self, task: str, memory: VIGAMemory, iteration: int) -> IterationContext:
        """
        Phase 1: Planning & Synthesis
        """
        # 1. Plan
        context_str = memory.get_full_prompt()
        plan = await self.skills.make_plan(task, context_str)
        
        # 2. Synthesis (Generate Code)
        latest_code = memory.get_latest_code()
        
        system_prompt = "You are an expert Blender Python scripter. Generate robust code."
        user_prompt = f"""Task: {task}
Current Plan: {plan}
Context History:
{context_str}

Latest Code:
```python
{latest_code}
```

Generate the next version of the code. Output full executable python code."""
        
        response = await self.model.generate_text(system_prompt, user_prompt)
        
        # Extract code using the fixed utility function
        code = extract_code_from_response(response)
            
        return IterationContext(
            iteration_id=iteration,
            plan=plan,
            code=code
        )


class VerifierAgent:
    def __init__(self, skills: SkillLibrary, model: FoundationModel):
        self.skills = skills
        self.model = model

    async def verify_step(self, task: str, ctx: IterationContext) -> str:
        """
        Phase 3: Verify (Active Exploration)
        """
        # 1. Initialize Viewpoint
        await self.skills.initialize_viewpoint()
        
        # 2. Active Exploration (Simplification: 1 step of investigation)
        scene_info = await self.skills.get_scene_info_text()
        
        # 3. Capture Observation (Screenshot)
        screenshot_res = await self.skills.mcp.get_viewport_screenshot()
        img_data = screenshot_res.get("image_data", "")
        
        # 4. Compare with Mental Model / Task
        system_prompt = "You are a Vision-as-Inverse-Graphics Verifier."
        user_prompt = f"""Task: {task}
Scene Info: {scene_info}
Verify if the rendered image matches the task. 
Provide specific feedback on geometry, placement, and materials.
Suggest specific fixes."""
        
        feedback = await self.model.generate_text(system_prompt, user_prompt, images=[img_data])
        
        return feedback


class VIGAAgent:
    def __init__(self, mcp_client: BlenderMCPClient, model_name: str = "qwen3-vl-30b"):
        self.mcp = mcp_client
        self.model = get_model(model_name)
        self.skills = SkillLibrary(mcp_client, self.model)
        self.memory = VIGAMemory(window_size=3)
        
        self.generator = GeneratorAgent(self.skills, self.model)
        self.verifier = VerifierAgent(self.skills, self.model)

    async def run_loop(self, task_instruction: str, max_iterations: int = 5):
        """
        Algorithm 1: VIGA Analysis-by-Synthesis Loop
        """
        self.memory.static_context["task"] = task_instruction
        
        for t in range(max_iterations):
            print(f"=== VIGA Iteration {t+1}/{max_iterations} ===")
            
            # Phase 1: Generator
            print("[Generator] Planning and Synthesizing...")
            ctx = await self.generator.generate_step(task_instruction, self.memory, t)
            
            # Phase 2: Environment Execution
            print("[Environment] Executing Code...")
            exec_result = await self.skills.execute_code(ctx.code)
            ctx.execution_result = str(exec_result)
            
            if exec_result.get("status") == "error":
                print(f"[Environment] Error: {exec_result.get('errors')}")
                ctx.visual_feedback = f"Execution Error: {exec_result.get('errors')}"
            else:
                # Phase 3: Verifier
                print("[Verifier] Inspecting Scene...")
                feedback = await self.verifier.verify_step(task_instruction, ctx)
                ctx.visual_feedback = feedback
                print(f"[Verifier] Feedback: {feedback[:100]}...")
            
            # Phase 4: Update Memory
            self.memory.add_iteration(ctx)
            
            # Check convergence (simplified)
            if "OBJECTIVE COMPLETE" in str(ctx.visual_feedback):
                print("Convergence reached.")
                break
                
        print("VIGA Process Complete")
        return self.memory
