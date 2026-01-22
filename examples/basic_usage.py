"""
Basic Usage Example: Creating a 3D scene with vision feedback
"""

import asyncio
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# Import Colossus modules
import sys
sys.path.append("../src")
from colossus_blender import (
    ColossusD5Orchestrator,
    WorkflowState,
    create_blender_client
)


async def main():
    """Basic example: Create a cyberpunk scene"""

    # 1. Initialize LLM clients
    print("[Setup] Initializing LLM clients...")

    claude_llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        temperature=0.7
    )

    gemini_vision = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.7
    )

    # 2. Connect to Blender MCP
    print("[Setup] Connecting to Blender...")

    blender_client = await create_blender_client(
        mode="socket",  # Use direct socket connection
        host="localhost",
        port=9876
    )

    # 3. Load system prompt
    with open("../prompts/blender_mcp_system_prompt.md", "r") as f:
        system_prompt = f.read()

    # 4. Create orchestrator
    print("[Setup] Creating ColossusD5 orchestrator...")

    orchestrator = ColossusD5Orchestrator(
        claude_llm=claude_llm,
        vision_llm=gemini_vision,
        blender_mcp_client=blender_client,
        system_prompt=system_prompt,
        gpu_mode="3090"  # Change to "5090" if you have it
    )

    # 5. Define user intent
    user_intent = """
    Create a cyberpunk street scene with:
    - Neon-lit buildings in the background
    - Wet asphalt ground with reflections
    - Holographic advertisements floating in the air
    - Dramatic purple and blue lighting
    - Camera at street level, slightly tilted up
    """

    # 6. Create workflow state
    state = WorkflowState(
        user_intent=user_intent,
        max_iterations=3,
        satisfaction_threshold=0.75
    )

    # 7. Run the workflow
    print(f"\n[Workflow] Starting scene creation...")
    print(f"User Intent: {user_intent}\n")

    final_state = await orchestrator.run(state)

    # 8. Print results
    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETE")
    print("=" * 60)
    print(f"Final Quality Score: {final_state.quality_score:.1%}")
    print(f"Iterations Used: {final_state.current_iteration + 1}/{final_state.max_iterations}")
    print(f"Goal Satisfied: {final_state.is_satisfied}")
    print(f"\nFinal Feedback:")
    print(f"  Positive: {final_state.visual_feedback.get('positive_aspects', [])}")
    print(f"  Issues: {final_state.visual_feedback.get('issues', [])}")

    # 9. Disconnect
    await blender_client.disconnect()
    print("\n[Cleanup] Disconnected from Blender")


if __name__ == "__main__":
    # Make sure you have:
    # 1. Blender running with the MCP addon enabled
    # 2. ANTHROPIC_API_KEY env var set
    # 3. GOOGLE_API_KEY env var set

    asyncio.run(main())
