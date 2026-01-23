"""
Advanced Usage: Multi-scene creation with custom agents
"""

import asyncio
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

import sys
sys.path.append("../src")
from colossus_blender import (
    ColossusD5Orchestrator,
    WorkflowState,
    create_blender_client,
    get_gpu_config
)


async def create_multiple_scenes():
    """Create multiple scenes and compare quality"""

    # Initialize
    claude = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    gemini = ChatGoogleGenerativeAI(model="gemini-2.5-pro")
    blender = await create_blender_client(mode="socket")

    with open("../prompts/blender_mcp_system_prompt.md", "r") as f:
        system_prompt = f.read()

    orchestrator = ColossusD5Orchestrator(
        claude_llm=claude,
        vision_llm=gemini,
        blender_mcp_client=blender,
        system_prompt=system_prompt,
        gpu_mode="3090"
    )

    # Define multiple scene intents
    scenes = [
        {
            "name": "Medieval Castle",
            "intent": "Medieval castle on a hill with stone walls, towers, flags, surrounded by forest",
            "threshold": 0.75
        },
        {
            "name": "Futuristic Lab",
            "intent": "High-tech laboratory with holographic displays, robotic arms, clean white surfaces",
            "threshold": 0.80
        },
        {
            "name": "Cozy Coffee Shop",
            "intent": "Warm coffee shop interior with wooden tables, plants, warm lighting, coffee machine",
            "threshold": 0.75
        }
    ]

    results = []

    for idx, scene in enumerate(scenes, 1):
        print(f"\n{'=' * 60}")
        print(f"Scene {idx}/{len(scenes)}: {scene['name']}")
        print(f"{'=' * 60}")

        # Clear scene first
        await blender.clear_scene(keep_camera=True)

        # Create state
        state = WorkflowState(
            user_intent=scene['intent'],
            max_iterations=3,
            satisfaction_threshold=scene['threshold']
        )

        # Run workflow
        final_state = await orchestrator.run(state)

        # Save results
        results.append({
            "scene_name": scene['name'],
            "quality_score": final_state.quality_score,
            "iterations": final_state.current_iteration + 1,
            "satisfied": final_state.is_satisfied,
            "feedback": final_state.visual_feedback
        })

        print(f"\nResult: {final_state.quality_score:.1%} quality, {final_state.current_iteration + 1} iterations")

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY OF ALL SCENES")
    print(f"{'=' * 60}")

    for result in results:
        print(f"\n{result['scene_name']}:")
        print(f"  Quality: {result['quality_score']:.1%}")
        print(f"  Iterations: {result['iterations']}")
        print(f"  Satisfied: {result['satisfied']}")

    avg_quality = sum(r['quality_score'] for r in results) / len(results)
    print(f"\nAverage Quality: {avg_quality:.1%}")

    await blender.disconnect()


async def benchmark_gpu_performance():
    """Benchmark GPU with different quality settings"""

    print("\n=== GPU Performance Benchmark ===")

    # Get GPU config
    gpu_config = get_gpu_config("3090")

    # Test different quality levels
    quality_levels = ["preview", "production", "final"]

    for quality in quality_levels:
        settings = gpu_config.get_optimal_settings(quality)

        print(f"\n{quality.upper()} Quality:")
        print(f"  Samples: {settings.samples}")
        print(f"  Tile Size: {settings.tile_size}x{settings.tile_size}")
        print(f"  Subdivisions: {settings.max_subdivisions}")
        print(f"  Resolution: {settings.resolution_percentage}%")

    # Generate and execute benchmark code
    blender = await create_blender_client(mode="socket")

    from colossus_blender.gpu_config import generate_gpu_benchmark_code

    benchmark_code = generate_gpu_benchmark_code()
    result = await blender.execute_code(benchmark_code)

    if result.get("status") == "success":
        print(f"\nBenchmark Results:")
        print(f"  Render Time: {result.get('render_time_seconds', 0):.2f}s")
        print(f"  Samples/Second: {result.get('samples_per_second', 0):.1f}")
    else:
        print(f"\nBenchmark failed: {result.get('errors')}")

    await blender.disconnect()


async def iterative_refinement_demo():
    """Demo: Show how refinement improves quality over iterations"""

    claude = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    gemini = ChatGoogleGenerativeAI(model="gemini-2.5-pro")
    blender = await create_blender_client(mode="socket")

    with open("../prompts/blender_mcp_system_prompt.md", "r") as f:
        system_prompt = f.read()

    orchestrator = ColossusD5Orchestrator(
        claude_llm=claude,
        vision_llm=gemini,
        blender_mcp_client=blender,
        system_prompt=system_prompt,
        gpu_mode="3090"
    )

    intent = "A glass sphere on a wooden table with dramatic side lighting and soft shadows"

    state = WorkflowState(
        user_intent=intent,
        max_iterations=5,  # Allow more iterations
        satisfaction_threshold=0.85  # Higher threshold
    )

    print("\n=== Iterative Refinement Demo ===")
    print(f"Goal: {intent}")
    print(f"Threshold: 85%\n")

    final_state = await orchestrator.run(state)

    # Show iteration-by-iteration improvement
    print("\n=== Iteration History ===")
    for i, iter_data in enumerate(final_state.iteration_history, 1):
        print(f"\nIteration {i}:")
        print(f"  Score: {iter_data.get('quality_score', 0):.1%}")
        print(f"  Issues: {iter_data.get('issues', [])}")
        print(f"  Improvements: {iter_data.get('suggestions', [])}")

    await blender.disconnect()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]

        if mode == "multi":
            asyncio.run(create_multiple_scenes())
        elif mode == "benchmark":
            asyncio.run(benchmark_gpu_performance())
        elif mode == "refine":
            asyncio.run(iterative_refinement_demo())
        else:
            print("Usage: python advanced_workflow.py [multi|benchmark|refine]")
    else:
        print("Available modes:")
        print("  multi     - Create multiple scenes and compare")
        print("  benchmark - Benchmark GPU performance")
        print("  refine    - Demo iterative refinement")
        print("\nUsage: python advanced_workflow.py <mode>")
