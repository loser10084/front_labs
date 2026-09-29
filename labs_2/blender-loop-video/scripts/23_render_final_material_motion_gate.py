"""Render the final-material animation gate and capture loop-state evidence."""

from pathlib import Path
import json
import time
import traceback

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BLEND_PATH = PROJECT / "blend" / "venus-restoration-v16-final-material-motion-gate.blend"
OUTPUT_DIR = PROJECT / "renders" / "previews" / "final-material-motion-gate"
REPORT_PATH = OUTPUT_DIR / "motion-gate-state.json"
FRAMES = (1, 76, 151, 226, 301)
OBSOLETE_PREFIXES = ("LOOP10_Ribbon_", "LOOP10_Trace_", "LOOP10_Shard_")


def rounded(values, digits=7):
    return [round(float(value), digits) for value in values]


def hide_obsolete_assets():
    hidden = []
    for obj in bpy.data.objects:
        if obj.name.startswith(OBSOLETE_PREFIXES):
            obj.hide_render = True
            obj.hide_viewport = True
            hidden.append(obj.name)
    return sorted(hidden)


def projected_bounds(scene, camera, obj):
    points = [world_to_camera_view(scene, camera, obj.matrix_world @ Vector(corner)) for corner in obj.bound_box]
    xs = [point.x for point in points]
    ys = [point.y for point in points]
    return {
        "x_min": round(min(xs), 6),
        "x_max": round(max(xs), 6),
        "y_min": round(min(ys), 6),
        "y_max": round(max(ys), 6),
    }


def object_state(obj):
    if obj is None:
        return None
    return {
        "location": rounded(obj.matrix_world.translation),
        "rotation_euler": rounded(obj.rotation_euler),
        "scale": rounded(obj.scale),
    }


def capture_state(scene, frame):
    camera = scene.camera
    statue = bpy.data.objects.get("VENUS_Hunyuan_Working")
    scan = bpy.data.objects.get("VENUS_Scan_Light")
    if camera is None or statue is None or scan is None:
        raise RuntimeError("Camera, statue, or scan light is missing")
    target = None
    for constraint in camera.constraints:
        if constraint.target is not None:
            target = constraint.target
            break
    dust = []
    for name in sorted(name for name in bpy.data.objects.keys() if name.startswith("VENUS_Dust_"))[:5]:
        dust.append({"name": name, "location": rounded(bpy.data.objects[name].matrix_world.translation)})
    material = statue.active_material
    return {
        "frame": frame,
        "camera": object_state(camera),
        "camera_lens": round(float(camera.data.lens), 7),
        "camera_target": {"name": target.name, **object_state(target)} if target else None,
        "statue_screen_bounds": projected_bounds(scene, camera, statue),
        "scan_light": {
            **object_state(scan),
            "energy": round(float(scan.data.energy), 7),
        },
        "dust_sample": dust,
        "material": material.name if material else None,
    }


def main():
    scene = bpy.context.scene
    statue = bpy.data.objects.get("VENUS_Hunyuan_Working")
    if statue is None or statue.active_material is None:
        raise RuntimeError("Final Venus material is missing")
    if statue.active_material.name != "VENUS_Restoration_Material_v9_CleanResin":
        raise RuntimeError(f"Unexpected active material: {statue.active_material.name}")
    if scene.camera is None or scene.camera.name != "VENUS_Hall_Camera":
        raise RuntimeError("The animated hall camera is not active")

    hidden = hide_obsolete_assets()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.fps = 30

    report = {
        "source_blend": bpy.data.filepath,
        "output_blend": str(BLEND_PATH),
        "frames": list(FRAMES),
        "resolution": [1280, 720],
        "fps": 30,
        "engine": scene.render.engine,
        "hidden_obsolete_objects": hidden,
        "states": [],
    }
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        state = capture_state(scene, frame)
        output = OUTPUT_DIR / f"final-material-motion-{frame:03d}.png"
        scene.render.filepath = str(output)
        started = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        state["render_seconds"] = round(time.perf_counter() - started, 3)
        state["output"] = str(output)
        report["states"].append(state)
        print({"frame": frame, "seconds": state["render_seconds"], "output": str(output)})

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    scene.frame_set(1)
    scene["VENUS_STAGE"] = "final_material_motion_gate"
    scene["VENUS_MOTION_GATE_REPORT"] = str(REPORT_PATH)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print({"blend": str(BLEND_PATH), "report": str(REPORT_PATH), "hidden_obsolete_count": len(hidden)})


try:
    main()
except Exception:
    traceback.print_exc()
    raise
