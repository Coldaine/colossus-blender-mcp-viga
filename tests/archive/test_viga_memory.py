# Tests for VIGA Memory Module
import pytest
from src.colossus_blender.viga.memory import VIGAMemory, IterationContext

class TestIterationContext:
    def test_create_minimal_context(self):
        ctx = IterationContext(iteration_id=0)
        assert ctx.iteration_id == 0
        assert ctx.plan is None

    def test_to_dict_serialization(self):
        ctx = IterationContext(iteration_id=2, plan="Test", code="print(1)")
        d = ctx.to_dict()
        assert d["iteration"] == 2

class TestVIGAMemory:
    def test_empty_memory(self):
        mem = VIGAMemory(window_size=3)
        assert len(mem.history) == 0

    def test_sliding_window_respects_size(self):
        mem = VIGAMemory(window_size=2)
        for i in range(5):
            mem.add_iteration(IterationContext(iteration_id=i, code=f"step_{i}"))
        window = mem.get_context_window()
        assert len(window) == 2
        assert window[0].iteration_id == 3

    def test_get_latest_code(self):
        mem = VIGAMemory(window_size=3)
        mem.add_iteration(IterationContext(iteration_id=0, code="first"))
        mem.add_iteration(IterationContext(iteration_id=1, code="latest"))
        assert mem.get_latest_code() == "latest"
