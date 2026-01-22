"""
Colossus Blender MCP - VIGA Entry Point
Usage: python main.py --task "A detailed description of the 3D scene"
"""

import asyncio
import argparse
import sys
import os
from dotenv import load_dotenv

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from colossus_blender.mcp_client import create_blender_client
from colossus_blender.viga.agent import VIGAAgent

async def run_viga(task: str, model_name: str, max_iters: int):
    """Initialize and run the VIGA loop"""
    load_dotenv()
    
    # Connect to Blender MCP (defaulting to localhost:9876)
    host = os.getenv("BLENDER_HOST", "localhost")
    port = int(os.getenv("BLENDER_PORT", "9876"))
    
    print(f"Connecting to Blender MCP at {host}:{port}...")
    try:
        mcp = await create_blender_client(mode="socket", host=host, port=port)
        
        # Initialize VIGA Agent
        agent = VIGAAgent(mcp_client=mcp, model_name=model_name)
        
        print(f"Starting VIGA Loop for task: '{task}'")
        print(f"Using Model: {model_name}")
        
        memory = await agent.run_loop(task_instruction=task, max_iterations=max_iters)
        
        print("\n=== FINAL RESULTS ===")
        print(f"Total Iterations: {len(memory.history)}")
        if memory.history:
            last_feedback = memory.history[-1].visual_feedback or "No feedback available."
            print(f"Final Feedback Summary: {last_feedback[:200]}...")
            
    except Exception as e:
        print(f"Error during VIGA execution: {e}")
    finally:
        print("Done.")

def main():
    parser = argparse.ArgumentParser(description="Colossus Blender VIGA Agent")
    parser.add_argument("--task", type=str, required=True, help="Description of the 3D scene to create")
    parser.add_argument("--model", type=str, default="qwen3-vl-30b", help="Model name (qwen3-vl-8b, qwen3-vl-30b, gemini)")
    parser.add_argument("--iters", type=int, default=5, help="Maximum iterations")
    
    args = parser.parse_args()
    
    asyncio.run(run_viga(args.task, args.model, args.iters))

if __name__ == "__main__":
    main()
