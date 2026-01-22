# Integration tests for VIGA Agent
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.colossus_blender.viga.agent import VIGAAgent, GeneratorAgent, VerifierAgent
from src.colossus_blender.viga.memory import VIGAMemory, IterationContext
from src.colossus_blender.viga.skills import SkillLibrary
from src.colossus_blender.viga.modern_models import MockModel, FoundationModel


class MockMCPClient:
    """Mock Blender MCP client for testing."""
    
    async def execute_code(self, code: str):
        return {"status": "success", "output": "Code executed"}
    
    async def get_viewport_screenshot(self, max_size=1024):
        return {"status": "success", "image_data": "fake_base64_image"}
    
    async def get_scene_info(self):
        return {"objects": [{"name": "Cube", "type": "MESH"}]}


class CodeOnlyMockModel(FoundationModel):
    """Mock that always returns Python code."""
    async def generate_text(self, system_prompt: str, user_prompt: str, images=None):
        return """```python
import bpy
bpy.ops.mesh.primitive_cube_add()
```"""


class TestGeneratorAgent:
    @pytest.mark.asyncio
    async def test_generate_step_creates_context(self):
        mock_mcp = MockMCPClient()
        model = MockModel()
        skills = SkillLibrary(mock_mcp, model)
        generator = GeneratorAgent(skills, model)
        memory = VIGAMemory(window_size=3)
        
        ctx = await generator.generate_step("Create a cube", memory, 0)
        
        assert ctx.iteration_id == 0
        assert ctx.plan is not None
        assert ctx.code is not None

    @pytest.mark.asyncio
    async def test_generate_step_extracts_python_code(self):
        mock_mcp = MockMCPClient()
        model = CodeOnlyMockModel()
        skills = SkillLibrary(mock_mcp, model)
        generator = GeneratorAgent(skills, model)
        memory = VIGAMemory(window_size=3)
        
        ctx = await generator.generate_step("Add mesh", memory, 0)
        
        # Should extract the Python code from triple backticks
        assert "bpy" in ctx.code
        assert "primitive_cube" in ctx.code
        assert "```" not in ctx.code  # Backticks should be stripped


class TestVerifierAgent:
    @pytest.mark.asyncio
    async def test_verify_step_returns_feedback(self):
        mock_mcp = MockMCPClient()
        model = MockModel()
        skills = SkillLibrary(mock_mcp, model)
        verifier = VerifierAgent(skills, model)
        
        ctx = IterationContext(iteration_id=0, code="test")
        feedback = await verifier.verify_step("Create cube", ctx)
        
        assert feedback is not None
        assert isinstance(feedback, str)


class TestVIGAAgentIntegration:
    @pytest.mark.asyncio
    async def test_run_loop_executes_iterations(self):
        mock_mcp = MockMCPClient()
        agent = VIGAAgent(mock_mcp, model_name="mock")
        
        memory = await agent.run_loop("Create a simple cube", max_iterations=2)
        
        assert len(memory.history) == 2
        assert memory.history[0].iteration_id == 0
        assert memory.history[1].iteration_id == 1

    @pytest.mark.asyncio
    async def test_run_loop_stores_feedback(self):
        mock_mcp = MockMCPClient()
        agent = VIGAAgent(mock_mcp, model_name="mock")
        
        memory = await agent.run_loop("Test task", max_iterations=1)
        
        ctx = memory.history[0]
        assert ctx.code is not None
        assert ctx.visual_feedback is not None

    @pytest.mark.asyncio
    async def test_memory_accumulates_across_iterations(self):
        mock_mcp = MockMCPClient()
        agent = VIGAAgent(mock_mcp, model_name="mock")
        
        memory = await agent.run_loop("Build scene", max_iterations=3)
        
        # Memory should have 3 entries
        assert len(memory.history) == 3
        # Each should have incrementing iteration IDs
        for i, ctx in enumerate(memory.history):
            assert ctx.iteration_id == i
