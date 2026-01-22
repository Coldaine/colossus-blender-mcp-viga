"""
Colossus Blender MCP Integration
Multi-agent vision-based 3D scene creation with Blender

Uses GLM-4.5V from Z.AI for vision-based scene evaluation
"""

from .orchestrator import (
    ColossusD5Orchestrator,
    WorkflowState,
    PlannerAgent,
    DesignerAgent,
    ExecutorAgent,
    EvaluatorAgent,
    RefinerAgent,
    create_scene_iteratively
)

from .mcp_client import (
    BlenderMCPClient,
    BlenderConfig,
    ConnectionMode,
    MCPToolCaller,
    create_blender_client
)

from .gpu_config import (
    GPUConfigurator,
    GPUModel,
    GPUSpecs,
    RenderSettings,
    get_gpu_config,
    compare_gpus
)

from .glm_vision import (
    GLMVisionClient,
    GLMConfig,
    evaluate_screenshot_with_glm
)

from .vision_evaluator import (
    ComparisonVisionClient,
    VisionModelConfig,
    evaluate_screenshot_with_local_vision
)

__version__ = "0.3.0"
__author__ = "Colossus Team"
__description__ = "Vision-based AI 3D scene generation with Blender MCP and local Qwen2.5-VL"

__all__ = [
    # Orchestrator
    "ColossusD5Orchestrator",
    "WorkflowState",
    "PlannerAgent",
    "DesignerAgent",
    "ExecutorAgent",
    "EvaluatorAgent",
    "RefinerAgent",
    "create_scene_iteratively",

    # MCP Client
    "BlenderMCPClient",
    "BlenderConfig",
    "ConnectionMode",
    "MCPToolCaller",
    "create_blender_client",

    # GPU Config
    "GPUConfigurator",
    "GPUModel",
    "GPUSpecs",
    "RenderSettings",
    "get_gpu_config",
    "compare_gpus",

    # Vision Models
    "GLMVisionClient",  # Legacy GLM-4.5V (for backward compatibility)
    "GLMConfig",
    "evaluate_screenshot_with_glm",
    "ComparisonVisionClient",  # New local Qwen2.5-VL
    "VisionModelConfig",
    "evaluate_screenshot_with_local_vision",
]
