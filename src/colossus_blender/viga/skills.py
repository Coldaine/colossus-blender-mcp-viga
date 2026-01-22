"""
VIGA Skill Library
Implements the Generation and Verification tools from Table 1 of arXiv:2601.11109v1
"""

import json
from typing import Dict, Any, List
# Adjust import based on relative path
from ..mcp_client import BlenderMCPClient
from .modern_models import FoundationModel

class SkillLibrary:
    def __init__(self, mcp_client: BlenderMCPClient, model: FoundationModel):
        self.mcp = mcp_client
        self.model = model

    # --- Generation Tools ---

    async def make_plan(self, task_description: str, context_memory: str) -> str:
        """
        Write an explicit high-level action plan before editing.
        """
        prompt = f"""Task: {task_description}
Context: {context_memory}
Create a step-by-step plan for the next iteration of Blender editing."""
        
        return await self.model.generate_text('You are a 3D planning agent.', prompt)

    async def execute_code(self, code: str) -> Dict[str, Any]:
        """
        Execute the current program to construct or update the scene.
        """
        return await self.mcp.execute_code(code)

    async def get_scene_info_text(self) -> str:
        """
        Query object attributes (semantic summary).
        """
        # We can reuse the get_scene_info from mcp_client and format it
        info = await self.mcp.get_scene_info()
        return json.dumps(info, indent=2)

    async def get_better_assets(self, query: str) -> str:
        """
        Retrieve or generate improved assets (Placeholder).
        In a full implementation, this calls Meshy/Tripo/Sketchfab APIs.
        """
        return f'# [Placeholder] Retrieved asset for {query} at assets/{query}.glb'

    # --- Verification Tools ---

    async def initialize_viewpoint(self):
        """
        Compute joint bounding box and position camera to frame all objects.
        Implements proper camera framing with configurable padding.
        """
        code = '''
import bpy
import mathutils
import math

# Calculate bounding box of all mesh objects
min_xyz = [float('inf')] * 3
max_xyz = [float('-inf')] * 3
dataset = [o for o in bpy.context.scene.objects if o.type == 'MESH']

if not dataset:
    print("No meshes found - using default camera position")
else:
    for obj in dataset:
        for v in obj.bound_box:
            world_v = obj.matrix_world @ mathutils.Vector(v)
            for i in range(3):
                min_xyz[i] = min(min_xyz[i], world_v[i])
                max_xyz[i] = max(max_xyz[i], world_v[i])
    
    # Calculate center and size
    center = mathutils.Vector([(min_xyz[i] + max_xyz[i]) / 2 for i in range(3)])
    size = mathutils.Vector([max_xyz[i] - min_xyz[i] for i in range(3)])
    max_dim = max(size.x, size.y, size.z)
    
    # Position camera to frame the scene with 20% padding
    cam = bpy.context.scene.camera
    if cam:
        # Calculate distance based on camera FOV and object size
        fov = cam.data.angle if hasattr(cam.data, 'angle') else 0.785  # ~45 degrees default
        distance = (max_dim * 1.2) / (2 * math.tan(fov / 2))
        distance = max(distance, max_dim * 2)  # Minimum distance
        
        # Position camera at 45-degree angle (isometric-ish view)
        angle = math.radians(45)
        elevation = math.radians(30)
        
        cam.location = (
            center.x + distance * math.cos(elevation) * math.cos(angle),
            center.y - distance * math.cos(elevation) * math.sin(angle),
            center.z + distance * math.sin(elevation)
        )
        
        # Point camera at center
        direction = center - cam.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam.rotation_euler = rot_quat.to_euler()
        
        print(f"Camera positioned at {cam.location}, pointing at {center}")
    else:
        print("No active camera in scene")
'''
        await self.mcp.execute_code(code)

    async def set_camera(self, location: List[float], rotation: List[float]):
        """Move the camera to a specified pose."""
        code = f'''
import bpy
cam = bpy.context.scene.camera
if cam:
    cam.location = {location}
    cam.rotation_euler = {rotation}
'''
        await self.mcp.execute_code(code)

    async def investigate(self, instruction: str):
        """
        Adjust camera using natural language commands.
        Uses LLM to translate natural language into Blender camera code.
        """
        # Fast path for common commands
        instruction_lower = instruction.lower().strip()
        quick_commands = {
            "rotate left": "bpy.context.scene.camera.rotation_euler[2] += 0.2",
            "rotate right": "bpy.context.scene.camera.rotation_euler[2] -= 0.2",
            "zoom in": "bpy.context.scene.camera.location[1] += 2.0",
            "zoom out": "bpy.context.scene.camera.location[1] -= 2.0",
            "look up": "bpy.context.scene.camera.rotation_euler[0] -= 0.1",
            "look down": "bpy.context.scene.camera.rotation_euler[0] += 0.1",
            "move up": "bpy.context.scene.camera.location[2] += 1.0",
            "move down": "bpy.context.scene.camera.location[2] -= 1.0",
            "front view": "bpy.context.scene.camera.rotation_euler = (1.5708, 0, 0)",
            "side view": "bpy.context.scene.camera.rotation_euler = (1.5708, 0, 1.5708)",
            "top view": "bpy.context.scene.camera.rotation_euler = (0, 0, 0)",
        }
        
        for cmd, code in quick_commands.items():
            if cmd in instruction_lower:
                await self.mcp.execute_code(f"import bpy\n{code}")
                return
        
        # Use LLM for complex camera instructions
        prompt = f"""Generate Blender Python code to adjust the camera based on this instruction:
"{instruction}"

Return ONLY the Python code, no explanation. The code should:
1. Import bpy
2. Access bpy.context.scene.camera
3. Modify location and/or rotation_euler as needed

Example output:
```python
import bpy
cam = bpy.context.scene.camera
cam.location[0] += 5.0
```"""
        
        response = await self.model.generate_text(
            "You are a Blender Python expert. Output only valid Python code.",
            prompt
        )
        
        # Extract code from response
        from ..vision_utils import extract_code_from_response
        code = extract_code_from_response(response)
        
        if code and "bpy" in code:
            await self.mcp.execute_code(code)

    async def set_visibility(self, object_name: str, visible: bool):
        """Toggle object visibility."""
        code = f'''
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.hide_viewport = {str(not visible)}
    obj.hide_render = {str(not visible)}
'''
        await self.mcp.execute_code(code)
