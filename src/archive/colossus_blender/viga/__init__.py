"""VIGA - Vision-as-Inverse-Graphics Agent

Implementation of the Analysis-by-Synthesis loop from arXiv:2601.11109v1.
Supports Qwen3-VL and Gemini 3 Pro vision-language models.
"""

from .memory import IterationContext, VIGAMemory
from .modern_models import FoundationModel, Qwen3VL, Gemini3Pro, MockModel, get_model
from .agent import GeneratorAgent, VerifierAgent, VIGAAgent
from .skills import SkillLibrary

__all__ = [
    # Memory
    "IterationContext",
    "VIGAMemory",
    # Models
    "FoundationModel",
    "Qwen3VL",
    "Gemini3Pro",
    "MockModel",
    "get_model",
    # Agents
    "GeneratorAgent",
    "VerifierAgent",
    "VIGAAgent",
    # Skills
    "SkillLibrary",
]
