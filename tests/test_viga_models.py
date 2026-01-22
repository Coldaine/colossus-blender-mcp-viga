# Tests for VIGA Modern Models
import pytest
from src.colossus_blender.viga.modern_models import (
    FoundationModel, Qwen3VL, Gemini3Pro, MockModel, get_model
)

class TestModelFactory:
    def test_get_qwen_model(self):
        model = get_model("qwen3-vl-30b")
        assert isinstance(model, Qwen3VL)

    def test_get_qwen_8b_model(self):
        model = get_model("qwen3-vl-8b")
        assert isinstance(model, Qwen3VL)
        assert "8B" in model.model_name

    def test_get_gemini_model(self):
        model = get_model("gemini-3-pro")
        assert isinstance(model, Gemini3Pro)

    def test_get_unknown_returns_mock(self):
        model = get_model("unknown-model")
        assert isinstance(model, MockModel)

class TestMockModel:
    @pytest.mark.asyncio
    async def test_mock_returns_plan_json(self):
        model = MockModel()
        response = await model.generate_text("sys", "Create a plan for...")
        assert "subtasks" in response or "json" in response.lower()

    @pytest.mark.asyncio
    async def test_mock_returns_python_code(self):
        model = MockModel()
        response = await model.generate_text("sys", "Generate code to add cube")
        assert "bpy" in response or "python" in response.lower()

class TestQwen3VLConfig:
    def test_default_endpoint(self):
        model = Qwen3VL(size="30B")
        assert "localhost" in model.endpoint or "127.0.0.1" in model.endpoint

    def test_model_name_format(self):
        model = Qwen3VL(size="8B")
        assert "Qwen3-VL-8B" in model.model_name
