"""Start the Blender MCP server after the UI and add-ons finish loading."""

import bpy
from pathlib import Path

LOG_PATH = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video\renders\previews\blender-mcp-startup.log")


def log(message):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as stream:
        stream.write(message + "\n")


def start_mcp_server():
    try:
        log("timer fired")
        if "blender_mcp" not in bpy.context.preferences.addons:
            log("enabling blender_mcp")
            bpy.ops.preferences.addon_enable(module="blender_mcp")
        log(f"addon enabled={ 'blender_mcp' in bpy.context.preferences.addons }")
        result = bpy.ops.blendermcp.start_server()
        log(f"start result={list(result)}")
    except Exception as exc:
        log(f"start error={exc!r}")
    return None


bpy.app.timers.register(start_mcp_server, first_interval=2.0)
