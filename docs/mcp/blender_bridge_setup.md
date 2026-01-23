# Blender Bridge Setup

This document describes how to use the `ahujasid/blender-mcp` server as the bridge between our agent and Blender.

## Strategy

We cloned the `ahujasid/blender-mcp` repository into `external/blender-mcp` and installed it as an **editable package** in our workspace. This allows us to:
- Customize tools and behavior as needed
- Develop without worrying about upstream updates
- Use it both locally and let VS Code see its tools

## Installation

Already done:
1. Repository cloned to `external/blender-mcp`
2. Installed as editable: `uv pip install -e external/blender-mcp`
3. Entry point: `blender-mcp` command (runs `blender_mcp.server:main`)

## Blender Addon

The Blender-side socket server is in `external/blender-mcp/addon.py`.

### Installing the addon:
1. Copy `external/blender-mcp/addon.py` to a known location (or reference it directly).
2. Open Blender 4.4+.
3. Go to **Edit > Preferences > Add-ons > Install**.
4. Select `addon.py`.
5. Enable **Interface: Blender MCP**.
6. In the 3D View sidebar (press `N`), find the "BlenderMCP" tab and click "Connect to Claude".

The addon starts a socket server on `localhost:9876` by default.

## VS Code Integration

To make the MCP server tools visible in VS Code (GitHub Copilot):

1. Ensure the workspace venv is active (`.venv/Scripts/python.exe`).
2. The `blender-mcp` package is already editable, so any changes to `external/blender-mcp/src/blender_mcp/server.py` will be reflected immediately.
3. For Copilot to see the tools, you may need to configure the MCP server in VS Code settings (exact mechanism TBD; typical flow is to add a `.vscode/mcp.json` or similar).

## Customization

The server defines tools in `external/blender-mcp/src/blender_mcp/server.py`. Current tools include:
- `execute_blender_code`
- `get_blender_scene_info`
- `get_viewport_screenshot`
- `search_sketchfab`
- `download_polyhaven_asset`
- `generate_rodin_model`
- `generate_hunyuan_model`

To disable a tool: comment out or remove its `@mcp.tool()` decorator.

To add a tool: define a new function with the `@mcp.tool()` decorator (or `@telemetry_tool` if you want telemetry).

## Environment Variables

The server reads:
- `BLENDER_HOST` (default: `localhost`)
- `BLENDER_PORT` (default: `9876`)

Set these in your OS environment or in a local `.env` file.

## Testing the Connection

Once Blender is running with the addon enabled:

```powershell
# In the workspace root
python -m blender_mcp.server
```

If the connection succeeds, you should see:
```
Connected to Blender at localhost:9876
```

## Next Steps

As we implement Phase I, we'll:
1. Use the existing tools (`execute_blender_code`, `get_viewport_screenshot`, `get_blender_scene_info`).
2. Add new tools as specified in the master requirements (e.g., `reset_to_baseline`, `export_blend`, `set_camera_pose`, `get_diagnostic_renders`).
3. Update this doc with any changes to the tool set or configuration.

## Related Docs

- Master requirements: [../MASTER_REQUIREMENTS.md](../MASTER_REQUIREMENTS.md)
- Phase I plan: [../plans/phase_1_mvp_inner_loop.md](../plans/phase_1_mvp_inner_loop.md)
- Upstream repo: https://github.com/ahujasid/blender-mcp
