"""
Game Asset Workflow Example
Demonstrates full pipeline from OBJ import to game-ready FBX export
"""

import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.colossus_blender import (
    create_blender_client,
    ComparisonVisionClient
)
from src.colossus_blender.game_asset_agent import GameAssetAgent
from src.colossus_blender.game_asset_config import get_profile


async def example_1_simple_battleship():
    """Example 1: Process a simple battleship mesh into game asset"""

    print("\n" + "=" * 70)
    print("EXAMPLE 1: Simple Battleship Game Asset Processing")
    print("=" * 70)

    # Connect to Blender
    print("\n[1/5] Connecting to Blender...")
    blender = await create_blender_client(mode="socket", host="localhost", port=9876)
    print("✓ Connected to Blender MCP server")

    # Get game profile
    print("\n[2/5] Loading game profile...")
    profile = get_profile("war_thunder")  # or "world_of_warships", "unity", "unreal"
    print(f"✓ Loaded profile: {profile.name}")
    print(f"  LOD Levels: {len(profile.lod_levels)}")
    print(f"  LOD0 Budget: {profile.lod_levels[0].max_triangles:,} triangles")

    # Create game asset agent
    print("\n[3/5] Initializing Game Asset Agent...")
    agent = GameAssetAgent(
        blender_mcp_client=blender,
        output_dir=Path("./outputs/game_assets")
    )
    print("✓ Agent initialized")

    # Process mesh (replace with actual file path)
    input_mesh = Path("./test_assets/simple_battleship.obj")

    if not input_mesh.exists():
        print(f"\n⚠ Input file not found: {input_mesh}")
        print(f"Please create a test mesh or provide a valid path")
        await blender.disconnect()
        return

    print(f"\n[4/5] Processing mesh: {input_mesh.name}")
    metadata = await agent.process_mesh(
        input_mesh_path=input_mesh,
        profile=profile,
        asset_name="USS_Iowa_BB61"
    )

    # Display results
    print(f"\n[5/5] Processing Complete!")
    print(f"\n{'='*70}")
    print(f"RESULTS:")
    print(f"{'='*70}")
    print(f"Asset Name: {metadata.asset_name}")
    print(f"Profile: {metadata.profile_name}")
    print(f"\nTopology:")
    print(f"  Original Triangles: {metadata.original_triangles:,}")
    print(f"  LOD0 Triangles: {metadata.lod0_triangles:,}")
    print(f"  LOD Count: {metadata.lod_count}")
    print(f"  Topology Quality: {metadata.topology_quality:.1%}")
    print(f"\nUVs:")
    print(f"  Coverage: {metadata.uv_coverage:.1%}")
    print(f"  Islands: {metadata.uv_islands}")
    print(f"  UV Quality: {metadata.uv_quality:.1%}")
    print(f"\nMaterials:")
    print(f"  Created: {', '.join(metadata.materials_created)}")
    print(f"\nExport:")
    print(f"  FBX: {metadata.fbx_path}")
    print(f"  Textures: {metadata.texture_dir}")
    print(f"\nQuality:")
    print(f"  Overall: {metadata.overall_quality:.1%}")
    print(f"  Passes Validation: {'✓ Yes' if metadata.passes_validation else '✗ No'}")

    if not metadata.passes_validation:
        print(f"\nValidation Issues:")
        for issue in metadata.validation_issues:
            print(f"  - {issue}")

    # Disconnect
    await blender.disconnect()
    print(f"\n{'='*70}")


async def example_2_batch_processing():
    """Example 2: Batch process multiple battleship meshes"""

    print("\n" + "=" * 70)
    print("EXAMPLE 2: Batch Processing Multiple Ships")
    print("=" * 70)

    # List of ships to process
    ships = [
        ("./test_assets/uss_iowa.obj", "USS_Iowa_BB61", "war_thunder"),
        ("./test_assets/uss_missouri.obj", "USS_Missouri_BB63", "war_thunder"),
        ("./test_assets/uss_wisconsin.obj", "USS_Wisconsin_BB64", "war_thunder"),
    ]

    # Connect to Blender
    blender = await create_blender_client(mode="socket")

    agent = GameAssetAgent(
        blender_mcp_client=blender,
        output_dir=Path("./outputs/game_assets/batch")
    )

    results = []

    for mesh_path, asset_name, profile_name in ships:
        input_path = Path(mesh_path)

        if not input_path.exists():
            print(f"\n⚠ Skipping {asset_name}: File not found")
            continue

        print(f"\n{'='*70}")
        print(f"Processing: {asset_name}")
        print(f"{'='*70}")

        profile = get_profile(profile_name)

        metadata = await agent.process_mesh(
            input_mesh_path=input_path,
            profile=profile,
            asset_name=asset_name
        )

        results.append({
            "name": asset_name,
            "triangles": metadata.lod0_triangles,
            "quality": metadata.overall_quality,
            "passed": metadata.passes_validation
        })

    # Summary
    print(f"\n{'='*70}")
    print(f"BATCH PROCESSING SUMMARY")
    print(f"{'='*70}")

    for result in results:
        status = "✓" if result["passed"] else "✗"
        print(f"{status} {result['name']:<30} {result['triangles']:>8,} tris  Quality: {result['quality']:.1%}")

    passed = sum(1 for r in results if r["passed"])
    print(f"\nTotal: {len(results)} ships processed, {passed} passed validation")

    await blender.disconnect()


async def example_3_with_vision_evaluation():
    """Example 3: Process with vision-based quality evaluation"""

    print("\n" + "=" * 70)
    print("EXAMPLE 3: Game Asset with Vision Evaluation")
    print("=" * 70)

    # Connect to Blender and vision model
    blender = await create_blender_client(mode="socket")

    print("\n[Optional] Initializing vision model...")
    try:
        vision_client = ComparisonVisionClient()
        print("✓ Vision model available")
    except Exception as e:
        print(f"⚠ Vision model not available: {e}")
        print("  Continuing without vision evaluation...")
        vision_client = None

    # Create agent with vision
    agent = GameAssetAgent(
        blender_mcp_client=blender,
        output_dir=Path("./outputs/game_assets"),
        vision_client=vision_client
    )

    input_mesh = Path("./test_assets/simple_battleship.obj")

    if input_mesh.exists():
        profile = get_profile("unity")

        # Optional: Provide reference images for comparison
        reference_images = []

        # If you have reference blueprints/photos, add them:
        # reference_images = [
        #     {"type": "blueprint_top", "data": base64_encoded_blueprint},
        #     {"type": "photo_starboard", "data": base64_encoded_photo}
        # ]

        metadata = await agent.process_mesh(
            input_mesh_path=input_mesh,
            profile=profile,
            asset_name="USS_Iowa_Unity",
            reference_images=reference_images
        )

        print(f"\nProcessing complete with vision evaluation")
        print(f"Overall quality: {metadata.overall_quality:.1%}")

    else:
        print(f"⚠ Test file not found: {input_mesh}")

    await blender.disconnect()


async def main():
    """Run all examples"""

    print("\n" + "=" * 70)
    print("COLOSSUS GAME ASSET WORKFLOW EXAMPLES")
    print("=" * 70)
    print("\nThese examples demonstrate the game asset pipeline:")
    print("  1. Simple battleship processing (War Thunder profile)")
    print("  2. Batch processing multiple ships")
    print("  3. Processing with vision evaluation")
    print("\n" + "=" * 70)

    # Choose which example to run
    print("\nSelect example to run:")
    print("  1 - Simple battleship (recommended for first run)")
    print("  2 - Batch processing")
    print("  3 - With vision evaluation")
    print("  a - All examples")

    try:
        choice = input("\nEnter choice (1/2/3/a): ").strip().lower()

        if choice == "1":
            await example_1_simple_battleship()
        elif choice == "2":
            await example_2_batch_processing()
        elif choice == "3":
            await example_3_with_vision_evaluation()
        elif choice == "a":
            await example_1_simple_battleship()
            await example_2_batch_processing()
            await example_3_with_vision_evaluation()
        else:
            print(f"Invalid choice: {choice}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
