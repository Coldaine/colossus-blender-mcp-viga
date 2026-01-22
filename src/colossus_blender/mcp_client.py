"""
Blender MCP Client Wrapper
Handles communication with Blender via Model Context Protocol (MCP)
Supports both direct socket communication and MCP tool calling
"""

import json
import socket
import asyncio
import base64
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class ConnectionMode(Enum):
    """MCP connection modes"""
    SOCKET = "socket"  # Direct TCP socket to Blender addon
    MCP_TOOLS = "mcp_tools"  # Via Claude/LLM MCP tools


@dataclass
class BlenderConfig:
    """Blender connection configuration"""
    host: str = "localhost"
    port: int = 9876
    timeout: float = 30.0
    connection_mode: ConnectionMode = ConnectionMode.SOCKET


class BlenderMCPClient:
    """
    Client for communicating with Blender via MCP

    Supports two modes:
    1. Direct socket connection to Blender addon (addon.py)
    2. MCP tool calling through Claude/LLM (when integrated with Claude Desktop)
    """

    def __init__(self, config: Optional[BlenderConfig] = None, mcp_tool_caller=None):
        self.config = config or BlenderConfig()
        self.mcp_tool_caller = mcp_tool_caller
        self.socket = None
        self._connected = False

    async def connect(self) -> bool:
        """Establish connection to Blender"""
        if self.config.connection_mode == ConnectionMode.SOCKET:
            return await self._connect_socket()
        else:
            # MCP tools don't require explicit connection
            return True

    async def _connect_socket(self) -> bool:
        """Connect via TCP socket"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.config.timeout)
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.socket.connect,
                (self.config.host, self.config.port)
            )
            self._connected = True
            print(f"[MCP Client] Connected to Blender at {self.config.host}:{self.config.port}")
            return True
        except Exception as e:
            print(f"[MCP Client] Connection failed: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """Close connection"""
        if self.socket:
            self.socket.close()
            self._connected = False

    async def execute_code(self, code: str) -> Dict[str, Any]:
        """
        Execute Python code in Blender

        Args:
            code: Python code to execute

        Returns:
            {
                "status": "success" | "error",
                "output": str,
                "errors": List[str],
                "result": Any (JSON-serializable)
            }
        """
        if self.config.connection_mode == ConnectionMode.SOCKET:
            return await self._execute_code_socket(code)
        else:
            return await self._execute_code_mcp_tools(code)

    async def _execute_code_socket(self, code: str) -> Dict[str, Any]:
        """Execute code via direct socket connection"""
        if not self._connected:
            await self.connect()

        try:
            # Prepare message
            message = {
                "command": "execute",
                "code": code
            }
            message_json = json.dumps(message) + "\n"

            # Send
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.socket.sendall,
                message_json.encode('utf-8')
            )

            # Receive response
            response_data = await asyncio.get_event_loop().run_in_executor(
                None,
                self._recv_until_newline
            )

            response = json.loads(response_data)
            return response

        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "errors": [str(e)],
                "result": None
            }

    def _recv_until_newline(self, buffer_size: int = 4096) -> str:
        """Receive data until newline"""
        data = b""
        while True:
            chunk = self.socket.recv(buffer_size)
            if not chunk:
                break
            data += chunk
            if b"\n" in data:
                break
        return data.decode('utf-8')

    async def _execute_code_mcp_tools(self, code: str) -> Dict[str, Any]:
        """Execute code via MCP tools (through Claude)"""
        if not self.mcp_tool_caller:
            return {
                "status": "error",
                "output": "",
                "errors": ["No MCP tool caller configured"],
                "result": None
            }

        try:
            # Call the blender MCP tool through the LLM
            result = await self.mcp_tool_caller.call_tool(
                tool_name="blender_execute_code",
                arguments={"code": code}
            )
            return result
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "errors": [str(e)],
                "result": None
            }

    async def get_viewport_screenshot(
        self,
        max_size: int = 1024,
        format: str = "png"
    ) -> Dict[str, Any]:
        """
        Capture viewport screenshot

        Args:
            max_size: Maximum dimension in pixels
            format: Image format (png, jpg)

        Returns:
            {
                "status": "success" | "error",
                "image_data": str (base64),
                "format": str,
                "width": int,
                "height": int
            }
        """
        if self.config.connection_mode == ConnectionMode.SOCKET:
            return await self._get_screenshot_socket(max_size, format)
        else:
            return await self._get_screenshot_mcp_tools(max_size)

    async def _get_screenshot_socket(
        self,
        max_size: int,
        format: str
    ) -> Dict[str, Any]:
        """Get screenshot via socket"""
        code = f"""
import bpy
import io
import base64
from PIL import Image

def capture_viewport():
    try:
        # Find 3D viewport
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area

                # Capture to temp file
                filepath = "C:/temp/blender_viewport.png"
                bpy.ops.screen.screenshot(override, filepath=filepath)

                # Load and resize
                img = Image.open(filepath)
                img.thumbnail(({max_size}, {max_size}), Image.LANCZOS)

                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format='{format.upper()}')
                img_bytes = buffer.getvalue()
                img_b64 = base64.b64encode(img_bytes).decode()

                return {{
                    "status": "success",
                    "image_data": img_b64,
                    "format": "{format}",
                    "width": img.width,
                    "height": img.height
                }}

        return {{"status": "error", "message": "No 3D viewport found"}}
    except Exception as e:
        return {{"status": "error", "message": str(e)}}

result = capture_viewport()
print(json.dumps(result))
"""
        return await self.execute_code(code)

    async def _get_screenshot_mcp_tools(self, max_size: int) -> Dict[str, Any]:
        """Get screenshot via MCP tools"""
        if not self.mcp_tool_caller:
            return {
                "status": "error",
                "message": "No MCP tool caller configured"
            }

        try:
            result = await self.mcp_tool_caller.call_tool(
                tool_name="get_viewport_screenshot",
                arguments={"max_size": max_size}
            )
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    async def get_scene_info(self) -> Dict[str, Any]:
        """Get information about current scene"""
        code = """
import bpy
import json

def get_scene_info():
    try:
        info = {
            "objects": [],
            "materials": [],
            "lights": [],
            "cameras": []
        }

        for obj in bpy.data.objects:
            obj_data = {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "rotation": list(obj.rotation_euler),
                "scale": list(obj.scale)
            }

            if obj.type == 'MESH':
                info["objects"].append(obj_data)
            elif obj.type == 'LIGHT':
                obj_data["energy"] = obj.data.energy
                obj_data["light_type"] = obj.data.type
                info["lights"].append(obj_data)
            elif obj.type == 'CAMERA':
                obj_data["lens"] = obj.data.lens
                info["cameras"].append(obj_data)

        for mat in bpy.data.materials:
            info["materials"].append({
                "name": mat.name,
                "use_nodes": mat.use_nodes
            })

        return {
            "status": "success",
            "scene_info": info
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

result = get_scene_info()
print(json.dumps(result))
"""
        return await self.execute_code(code)

    async def clear_scene(self, keep_camera: bool = True) -> Dict[str, Any]:
        """Clear all objects from scene"""
        keep_types = ["'CAMERA'", "'LIGHT'"] if keep_camera else ["'LIGHT'"]
        keep_condition = f"obj.type not in [{', '.join(keep_types)}]"

        code = f"""
import bpy
import json

def clear_scene():
    try:
        bpy.ops.object.select_all(action='DESELECT')

        for obj in bpy.data.objects:
            if {keep_condition}:
                obj.select_set(True)

        bpy.ops.object.delete()

        # Purge orphan data
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        return {{"status": "success", "message": "Scene cleared"}}
    except Exception as e:
        return {{"status": "error", "message": str(e)}}

result = clear_scene()
print(json.dumps(result))
"""
        return await self.execute_code(code)

    async def download_model(
        self,
        source: str,
        model_id: str,
        import_location: tuple = (0, 0, 0)
    ) -> Dict[str, Any]:
        """
        Download and import 3D model from external source

        Args:
            source: "polyhaven" | "sketchfab" | "hyper3d"
            model_id: Model identifier
            import_location: Where to place the model

        Returns:
            Status dict
        """
        code = f"""
import bpy
import json
# Note: Actual implementation would require API integration
# This is a template for the MCP addon to implement

def download_model():
    try:
        # TODO: Implement model download via {source}
        # Model ID: {model_id}
        # Location: {import_location}

        return {{
            "status": "not_implemented",
            "message": "Model download requires MCP addon support",
            "source": "{source}",
            "model_id": "{model_id}"
        }}
    except Exception as e:
        return {{"status": "error", "message": str(e)}}

result = download_model()
print(json.dumps(result))
"""
        return await self.execute_code(code)


class MCPToolCaller:
    """
    Adapter for calling MCP tools through LLM clients
    Used when integrating with Claude Desktop or similar
    """

    def __init__(self, llm_client):
        self.llm = llm_client

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool through the LLM

        Args:
            tool_name: Name of the MCP tool
            arguments: Tool arguments

        Returns:
            Tool result
        """
        # This would be implemented based on the specific LLM client
        # For Claude, it would use the tools parameter in messages.create()
        raise NotImplementedError("Implement based on your LLM client")


# Convenience functions
async def create_blender_client(
    mode: str = "socket",
    host: str = "localhost",
    port: int = 9876,
    mcp_tool_caller=None
) -> BlenderMCPClient:
    """
    Create and connect a Blender MCP client

    Args:
        mode: "socket" or "mcp_tools"
        host: Blender host (for socket mode)
        port: Blender port (for socket mode)
        mcp_tool_caller: Tool caller instance (for mcp_tools mode)

    Returns:
        Connected BlenderMCPClient
    """
    connection_mode = ConnectionMode.SOCKET if mode == "socket" else ConnectionMode.MCP_TOOLS

    config = BlenderConfig(
        host=host,
        port=port,
        connection_mode=connection_mode
    )

    client = BlenderMCPClient(config=config, mcp_tool_caller=mcp_tool_caller)
    await client.connect()

    return client
