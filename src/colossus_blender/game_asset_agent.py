"""
Game Asset Agent
Transforms Blender scenes/meshes into game-ready assets with LODs, UVs, PBR materials, and optimized topology
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .game_asset_config import (
    GameAssetProfile,
    get_profile,
    LODLevel,
    MaterialProfile,
    ExportFormat
)


@dataclass
class GameAssetMetadata:
    """Metadata for a processed game asset"""
    asset_name: str
    profile_name: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Topology stats
    original_triangles: int = 0
    lod0_triangles: int = 0
    lod_count: int = 0

    # UV stats
    uv_coverage: float = 0.0
    uv_islands: int = 0

    # Material stats
    materials_created: List[str] = field(default_factory=list)
    textures_baked: List[str] = field(default_factory=list)

    # Export info
    fbx_path: Optional[str] = None
    texture_dir: Optional[str] = None

    # Quality metrics
    topology_quality: float = 0.0  # 0-1 score
    uv_quality: float = 0.0  # 0-1 score
    overall_quality: float = 0.0  # 0-1 score

    # Validation
    passes_validation: bool = False
    validation_issues: List[str] = field(default_factory=list)


class GameAssetAgent:
    """
    Converts Blender scenes/meshes into game-ready assets

    Pipeline stages:
    1. Import/validate input mesh
    2. Topology cleanup (remove n-gons, optimize edge flow)
    3. UV unwrapping (Smart UV project + optimization)
    4. PBR material generation (naval-specific materials)
    5. Normal map baking (high-poly to low-poly)
    6. LOD generation (4 levels with Decimate modifier)
    7. FBX export (game engine compatible)
    8. Quality validation
    """

    def __init__(
        self,
        blender_mcp_client,
        output_dir: Path = Path("./outputs/game_assets"),
        vision_client=None
    ):
        self.blender_mcp = blender_mcp_client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.vision_client = vision_client  # Optional: for quality evaluation

    async def process_mesh(
        self,
        input_mesh_path: Path,
        profile: GameAssetProfile,
        asset_name: Optional[str] = None,
        reference_images: Optional[List[Dict[str, str]]] = None
    ) -> GameAssetMetadata:
        """
        Process a mesh file into a game-ready asset

        Args:
            input_mesh_path: Path to input OBJ/FBX/BLEND file
            profile: Game asset profile (War Thunder, Unity, etc.)
            asset_name: Optional custom name (defaults to input filename)
            reference_images: Optional reference images for vision evaluation

        Returns:
            GameAssetMetadata with processing results
        """

        if asset_name is None:
            asset_name = input_mesh_path.stem

        print(f"[GameAssetAgent] Processing: {asset_name}")
        print(f"[GameAssetAgent] Profile: {profile.name}")
        print(f"[GameAssetAgent] Input: {input_mesh_path}")

        metadata = GameAssetMetadata(
            asset_name=asset_name,
            profile_name=profile.name
        )

        # Stage 1: Import mesh
        print(f"\n[1/8] Importing mesh...")
        await self._import_mesh(input_mesh_path)
        original_stats = await self._get_mesh_stats()
        metadata.original_triangles = original_stats.get("triangles", 0)
        print(f"  Original triangles: {metadata.original_triangles:,}")

        # Stage 2: Topology cleanup
        print(f"\n[2/8] Cleaning up topology...")
        topology_result = await self._cleanup_topology(profile)
        metadata.topology_quality = topology_result.get("quality_score", 0.0)
        print(f"  Topology quality: {metadata.topology_quality:.1%}")

        # Stage 3: UV unwrapping
        print(f"\n[3/8] UV unwrapping...")
        uv_result = await self._unwrap_uvs(profile)
        metadata.uv_coverage = uv_result.get("coverage", 0.0)
        metadata.uv_islands = uv_result.get("islands", 0)
        metadata.uv_quality = uv_result.get("quality_score", 0.0)
        print(f"  UV coverage: {metadata.uv_coverage:.1%}")
        print(f"  UV islands: {metadata.uv_islands}")

        # Stage 4: PBR materials
        print(f"\n[4/8] Generating PBR materials...")
        material_result = await self._generate_pbr_materials(profile)
        metadata.materials_created = material_result.get("materials", [])
        print(f"  Materials created: {len(metadata.materials_created)}")

        # Stage 5: Normal map baking (optional, if high-poly source available)
        print(f"\n[5/8] Baking normal maps...")
        bake_result = await self._bake_normal_maps(profile)
        metadata.textures_baked = bake_result.get("textures", [])
        if metadata.textures_baked:
            print(f"  Textures baked: {len(metadata.textures_baked)}")
        else:
            print(f"  Skipped (no high-poly source)")

        # Stage 6: LOD generation
        print(f"\n[6/8] Generating LOD levels...")
        lod_result = await self._generate_lods(profile)
        metadata.lod_count = lod_result.get("lod_count", 0)
        metadata.lod0_triangles = lod_result.get("lod0_triangles", 0)
        print(f"  LOD levels created: {metadata.lod_count}")
        for lod_name, tris in lod_result.get("lod_stats", {}).items():
            print(f"    {lod_name}: {tris:,} triangles")

        # Stage 7: Export FBX
        print(f"\n[7/8] Exporting FBX...")
        export_result = await self._export_game_asset(
            asset_name=asset_name,
            profile=profile
        )
        metadata.fbx_path = export_result.get("fbx_path")
        metadata.texture_dir = export_result.get("texture_dir")
        print(f"  FBX exported: {metadata.fbx_path}")
        print(f"  Textures: {metadata.texture_dir}")

        # Stage 8: Validation
        print(f"\n[8/8] Validating asset...")
        validation_result = await self._validate_game_asset(profile, metadata)
        metadata.passes_validation = validation_result.get("passes", False)
        metadata.validation_issues = validation_result.get("issues", [])
        metadata.overall_quality = validation_result.get("overall_quality", 0.0)

        if metadata.passes_validation:
            print(f"  ✓ Asset passes validation")
        else:
            print(f"  ⚠ Validation issues found: {len(metadata.validation_issues)}")
            for issue in metadata.validation_issues[:5]:
                print(f"    - {issue}")

        print(f"\n[GameAssetAgent] Overall quality: {metadata.overall_quality:.1%}")
        print(f"[GameAssetAgent] Processing complete!")

        # Save metadata
        metadata_path = self.output_dir / f"{asset_name}_metadata.json"
        self._save_metadata(metadata, metadata_path)

        return metadata

    async def _import_mesh(self, mesh_path: Path):
        """Import mesh into Blender"""
        extension = mesh_path.suffix.lower()

        if extension == ".obj":
            import_code = f'''
import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import OBJ
bpy.ops.import_scene.obj(filepath=r"{mesh_path}")

print("OBJ import successful")
'''
        elif extension == ".fbx":
            import_code = f'''
import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.import_scene.fbx(filepath=r"{mesh_path}")

print("FBX import successful")
'''
        elif extension == ".blend":
            # For .blend files, append objects
            import_code = f'''
import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Append all objects from .blend file
with bpy.data.libraries.load(r"{mesh_path}") as (data_from, data_to):
    data_to.objects = data_from.objects

for obj in data_to.objects:
    if obj is not None:
        bpy.context.collection.objects.link(obj)

print("BLEND import successful")
'''
        else:
            raise ValueError(f"Unsupported file format: {extension}")

        result = await self.blender_mcp.execute_code(import_code)
        if result.get("status") != "success":
            raise Exception(f"Import failed: {result.get('errors', [])}")

    async def _get_mesh_stats(self) -> Dict[str, Any]:
        """Get statistics about the current mesh"""
        stats_code = '''
import bpy
import json

obj = bpy.context.active_object
if obj and obj.type == 'MESH':
    mesh = obj.data
    mesh.calc_loop_triangles()

    stats = {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "faces": len(mesh.polygons),
        "triangles": len(mesh.loop_triangles),
        "has_uvs": len(mesh.uv_layers) > 0,
        "materials": len(obj.material_slots)
    }
    print(json.dumps(stats))
else:
    print(json.dumps({"error": "No active mesh object"}))
'''
        result = await self.blender_mcp.execute_code(stats_code)
        if result.get("status") == "success":
            output = result.get("output", "{}")
            # Parse last line of output as JSON
            lines = output.strip().split('\n')
            return json.loads(lines[-1])
        return {}

    async def _cleanup_topology(self, profile: GameAssetProfile) -> Dict[str, Any]:
        """Clean up mesh topology (remove doubles, dissolve n-gons, etc.)"""
        cleanup_code = f'''
import bpy
import json

obj = bpy.context.active_object
if obj and obj.type == 'MESH':
    # Enter edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # Remove doubles
    bpy.ops.mesh.remove_doubles(threshold=0.0001)

    # Dissolve degenerate edges
    bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)

    # Convert n-gons to triangles/quads if needed
    {"bpy.ops.mesh.tris_convert_to_quads()" if profile.prefer_quads else ""}

    # Recalculate normals
    bpy.ops.mesh.normals_make_consistent(inside=False)

    # Exit edit mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Get updated stats
    mesh = obj.data
    mesh.calc_loop_triangles()

    ngon_count = sum(1 for p in mesh.polygons if len(p.vertices) > 4)
    tri_count = sum(1 for p in mesh.polygons if len(p.vertices) == 3)
    quad_count = sum(1 for p in mesh.polygons if len(p.vertices) == 4)

    quality_score = 1.0
    if ngon_count > 0 and not {str(profile.allow_ngons).lower()}:
        quality_score -= 0.3
    if tri_count > quad_count and {str(profile.prefer_quads).lower()}:
        quality_score -= 0.2

    result = {{
        "ngons": ngon_count,
        "tris": tri_count,
        "quads": quad_count,
        "quality_score": max(0.0, quality_score)
    }}

    print(json.dumps(result))
else:
    print(json.dumps({{"error": "No active mesh"}}))
'''
        result = await self.blender_mcp.execute_code(cleanup_code)
        if result.get("status") == "success":
            output = result.get("output", "{}")
            lines = output.strip().split('\n')
            return json.loads(lines[-1])
        return {"quality_score": 0.0}

    async def _unwrap_uvs(self, profile: GameAssetProfile) -> Dict[str, Any]:
        """Unwrap UVs using Smart UV Project"""
        unwrap_code = f'''
import bpy
import json
import math

obj = bpy.context.active_object
if obj and obj.type == 'MESH':
    # Enter edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # Smart UV Project
    bpy.ops.uv.smart_project(
        angle_limit=math.radians(66.0),
        island_margin=0.02,
        area_weight=1.0
    )

    # Pack UV islands
    bpy.ops.uv.pack_islands(margin=0.01)

    # Exit edit mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Calculate UV coverage
    mesh = obj.data
    if mesh.uv_layers:
        uv_layer = mesh.uv_layers.active.data

        # Simple coverage estimation
        # Count unique UV coordinates in 0-1 range
        uv_coords = set()
        for loop in mesh.loops:
            uv = uv_layer[loop.index].uv
            uv_coords.add((int(uv.x * 100), int(uv.y * 100)))

        coverage = len(uv_coords) / 10000.0  # Normalize to 0-1

        # Count islands (approximate)
        islands = len(mesh.uv_layers)

        quality_score = coverage
        if coverage < {profile.min_uv_coverage}:
            quality_score *= 0.7

        result = {{
            "coverage": coverage,
            "islands": islands,
            "quality_score": quality_score
        }}
    else:
        result = {{
            "coverage": 0.0,
            "islands": 0,
            "quality_score": 0.0,
            "error": "No UV layer created"
        }}

    print(json.dumps(result))
else:
    print(json.dumps({{"error": "No active mesh"}}))
'''
        result = await self.blender_mcp.execute_code(unwrap_code)
        if result.get("status") == "success":
            output = result.get("output", "{}")
            lines = output.strip().split('\n')
            return json.loads(lines[-1])
        return {"coverage": 0.0, "quality_score": 0.0}

    async def _generate_pbr_materials(self, profile: GameAssetProfile) -> Dict[str, Any]:
        """Generate PBR materials for the mesh"""

        # Create materials code
        materials_code = '''
import bpy
import json

obj = bpy.context.active_object
if obj and obj.type == 'MESH':
    materials_created = []

'''
        # Add each material from profile
        for mat_key, mat_prof in profile.materials.items():
            materials_code += f'''
    # Create {mat_prof.name}
    mat = bpy.data.materials.new(name="{mat_prof.name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = {mat_prof.base_color}
        bsdf.inputs['Metallic'].default_value = {mat_prof.metallic}
        bsdf.inputs['Roughness'].default_value = {mat_prof.roughness}
    materials_created.append("{mat_prof.name}")

'''

        materials_code += '''
    # Assign first material to object if it has none
    if len(obj.material_slots) == 0 and materials_created:
        mat_name = materials_created[0]
        mat = bpy.data.materials.get(mat_name)
        if mat:
            obj.data.materials.append(mat)

    print(json.dumps({"materials": materials_created}))
else:
    print(json.dumps({"materials": [], "error": "No active mesh"}))
'''

        result = await self.blender_mcp.execute_code(materials_code)
        if result.get("status") == "success":
            output = result.get("output", "{}")
            lines = output.strip().split('\n')
            return json.loads(lines[-1])
        return {"materials": []}

    async def _bake_normal_maps(self, profile: GameAssetProfile) -> Dict[str, Any]:
        """Bake normal maps (if high-poly source exists)"""
        # Placeholder for now - normal baking requires high-poly/low-poly pair
        # This would be implemented if we have a high-detail source mesh
        return {"textures": [], "note": "Normal baking requires high-poly source"}

    async def _generate_lods(self, profile: GameAssetProfile) -> Dict[str, Any]:
        """Generate LOD levels using Decimate modifier"""

        lod_code = '''
import bpy
import json

obj = bpy.context.active_object
if obj and obj.type == 'MESH':
    lod_stats = {}
    lod_objects = []

    # LOD0 is the original object
    obj.name = "LOD0"
    mesh = obj.data
    mesh.calc_loop_triangles()
    lod_stats["LOD0"] = len(mesh.loop_triangles)

    # Create additional LODs
'''

        for i, lod in enumerate(profile.lod_levels[1:], start=1):
            lod_code += f'''
    # Create LOD{i}
    lod_obj = obj.copy()
    lod_obj.data = obj.data.copy()
    lod_obj.name = "LOD{i}"
    bpy.context.collection.objects.link(lod_obj)

    # Add Decimate modifier
    decimate = lod_obj.modifiers.new(name="Decimate_LOD{i}", type='DECIMATE')
    decimate.ratio = {lod.reduction_ratio}
    decimate.use_collapse_triangulate = True

    # Apply modifier
    bpy.context.view_layer.objects.active = lod_obj
    bpy.ops.object.modifier_apply(modifier="Decimate_LOD{i}")

    # Get stats
    lod_obj.data.calc_loop_triangles()
    lod_stats["LOD{i}"] = len(lod_obj.data.loop_triangles)
    lod_objects.append("LOD{i}")

'''

        lod_code += f'''
    result = {{
        "lod_count": {len(profile.lod_levels)},
        "lod0_triangles": lod_stats.get("LOD0", 0),
        "lod_stats": lod_stats,
        "lod_objects": lod_objects
    }}

    print(json.dumps(result))
else:
    print(json.dumps({{"lod_count": 0, "error": "No active mesh"}}))
'''

        result = await self.blender_mcp.execute_code(lod_code)
        if result.get("status") == "success":
            output = result.get("output", "{}")
            lines = output.strip().split('\n')
            return json.loads(lines[-1])
        return {"lod_count": 0}

    async def _export_game_asset(
        self,
        asset_name: str,
        profile: GameAssetProfile
    ) -> Dict[str, str]:
        """Export game asset as FBX with textures"""

        output_path = self.output_dir / f"{asset_name}.fbx"
        texture_dir = self.output_dir / f"{asset_name}_textures"

        # Convert export settings to Blender API format
        export_settings = profile.export_settings.copy()

        export_code = f'''
import bpy
import json

# Select all LOD objects
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.data.objects:
    if obj.name.startswith("LOD"):
        obj.select_set(True)

# Export FBX
output_path = r"{output_path}"
bpy.ops.export_scene.fbx(
    filepath=output_path,
    use_selection=True,
    object_types={{'MESH'}},
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='{export_settings.get("axis_forward", "-Z")}',
    axis_up='{export_settings.get("axis_up", "Y")}',
    bake_anim={str(export_settings.get("bake_anim", False)).lower()},
    path_mode='{export_settings.get("path_mode", "COPY")}',
    embed_textures={str(export_settings.get("embed_textures", False)).lower()}
)

result = {{
    "fbx_path": output_path,
    "texture_dir": r"{texture_dir}"
}}

print(json.dumps(result))
'''

        result = await self.blender_mcp.execute_code(export_code)
        if result.get("status") == "success":
            output = result.get("output", "{}")
            lines = output.strip().split('\n')
            return json.loads(lines[-1])
        return {"fbx_path": str(output_path), "texture_dir": str(texture_dir)}

    async def _validate_game_asset(
        self,
        profile: GameAssetProfile,
        metadata: GameAssetMetadata
    ) -> Dict[str, Any]:
        """Validate the game asset meets quality requirements"""

        issues = []

        # Check triangle counts
        if metadata.lod0_triangles > profile.lod_levels[0].max_triangles:
            issues.append(
                f"LOD0 exceeds triangle budget: "
                f"{metadata.lod0_triangles:,} > {profile.lod_levels[0].max_triangles:,}"
            )

        # Check UV coverage
        if metadata.uv_coverage < profile.min_uv_coverage:
            issues.append(
                f"UV coverage too low: "
                f"{metadata.uv_coverage:.1%} < {profile.min_uv_coverage:.1%}"
            )

        # Check LOD count
        if metadata.lod_count < len(profile.lod_levels):
            issues.append(
                f"Missing LOD levels: "
                f"{metadata.lod_count} < {len(profile.lod_levels)}"
            )

        # Check materials
        if not metadata.materials_created and profile.materials:
            issues.append("No materials created")

        # Calculate overall quality
        topology_weight = 0.3
        uv_weight = 0.4
        lod_weight = 0.3

        overall_quality = (
            metadata.topology_quality * topology_weight +
            metadata.uv_quality * uv_weight +
            (metadata.lod_count / len(profile.lod_levels)) * lod_weight
        )

        passes = len(issues) == 0 and overall_quality >= 0.75

        return {
            "passes": passes,
            "issues": issues,
            "overall_quality": overall_quality
        }

    def _save_metadata(self, metadata: GameAssetMetadata, output_path: Path):
        """Save metadata to JSON file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        metadata_dict = {
            "asset_name": metadata.asset_name,
            "profile_name": metadata.profile_name,
            "created_at": metadata.created_at,
            "topology": {
                "original_triangles": metadata.original_triangles,
                "lod0_triangles": metadata.lod0_triangles,
                "lod_count": metadata.lod_count
            },
            "uvs": {
                "coverage": metadata.uv_coverage,
                "islands": metadata.uv_islands
            },
            "materials": metadata.materials_created,
            "textures": metadata.textures_baked,
            "export": {
                "fbx_path": metadata.fbx_path,
                "texture_dir": metadata.texture_dir
            },
            "quality": {
                "topology": metadata.topology_quality,
                "uv": metadata.uv_quality,
                "overall": metadata.overall_quality
            },
            "validation": {
                "passes": metadata.passes_validation,
                "issues": metadata.validation_issues
            }
        }

        with open(output_path, 'w') as f:
            json.dump(metadata_dict, f, indent=2)

        print(f"[GameAssetAgent] Metadata saved: {output_path}")


# Convenience function
async def process_battleship_mesh(
    mesh_path: Path,
    profile_name: str,
    blender_mcp_client,
    output_dir: Path = Path("./outputs/game_assets")
) -> GameAssetMetadata:
    """
    Quick helper to process a battleship mesh into a game asset

    Args:
        mesh_path: Path to input mesh (OBJ/FBX/BLEND)
        profile_name: Game profile name ("war_thunder", "world_of_warships", etc.)
        blender_mcp_client: Connected Blender MCP client
        output_dir: Output directory for processed assets

    Returns:
        GameAssetMetadata with processing results
    """

    profile = get_profile(profile_name)
    agent = GameAssetAgent(
        blender_mcp_client=blender_mcp_client,
        output_dir=output_dir
    )

    return await agent.process_mesh(
        input_mesh_path=mesh_path,
        profile=profile
    )
