"""Choreograph a continuous 10-second camera story and render its five keyframes."""

from pathlib import Path
import json
import time
import traceback

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BLEND_PATH = PROJECT / "blend" / "venus-restoration-v17-cinematic-camera.blend"
OUTPUT_DIR = PROJECT / "renders" / "previews" / "cinematic-motion-storyboard"
REPORT_PATH = OUTPUT_DIR / "storyboard-camera-report.json"
FRAMES = (1, 76, 151, 226, 301)
OBSOLETE_PREFIXES = ("LOOP10_Ribbon_", "LOOP10_Trace_", "LOOP10_Shard_")

# Story beat, camera location, target, and focal length. The last beat closes
# exactly on the opening wide composition; the animation between them remains
# one continuous eased camera move.
SHOTS = (
    {
        "frame": 1,
        "beat": "展厅建立：完整雕像与仪式空间",
        "location": (0.0, -10.35, 2.42),
        "target": (0.62, 0.0, 1.72),
        "lens": 48.0,
    },
    {
        "frame": 76,
        "beat": "接近面容：从展厅推进到头像与肩部",
        "location": (0.18, -5.55, 3.04),
        "target": (1.22, 0.0, 2.91),
        "lens": 61.0,
    },
    {
        "frame": 151,
        "beat": "修复揭示：胸腹的大理石与黑曜石交界",
        "location": (3.22, -5.35, 2.24),
        "target": (1.48, 0.0, 2.02),
        "lens": 61.0,
    },
    {
        "frame": 226,
        "beat": "沿修复带下移：树脂、金属与石质长袍",
        "location": (3.18, -5.05, 1.22),
        "target": (1.45, 0.0, 1.02),
        "lens": 64.0,
    },
    {
        "frame": 301,
        "beat": "回到展厅全景：无缝回环",
        "location": (0.0, -10.35, 2.42),
        "target": (0.62, 0.0, 1.72),
        "lens": 48.0,
    },
)


def rounded(values, digits=6):
    return [round(float(value), digits) for value in values]


def hide_obsolete_assets():
    hidden = []
    for obj in bpy.data.objects:
        if obj.name.startswith(OBSOLETE_PREFIXES):
            obj.hide_render = True
            obj.hide_viewport = True
            hidden.append(obj.name)
    return sorted(hidden)


def remove_all_drivers(owner, path):
    if owner is None or owner.animation_data is None:
        return
    for curve in list(owner.animation_data.drivers):
        if curve.data_path == path:
            owner.driver_remove(path, curve.array_index)


def configure_interpolation(owner, path, manual_loop_endpoints=False):
    animation = owner.animation_data
    if animation is None or animation.action is None:
        return
    for curve in animation.action.fcurves:
        if curve.data_path != path:
            continue
        for point in curve.keyframe_points:
            point.interpolation = "BEZIER"
            point.handle_left_type = "AUTO_CLAMPED"
            point.handle_right_type = "AUTO_CLAMPED"
        if manual_loop_endpoints and curve.keyframe_points:
            first = min(curve.keyframe_points, key=lambda item: item.co.x)
            last = max(curve.keyframe_points, key=lambda item: item.co.x)
            # Match the endpoint tangents so frame 300 flows into frame 1
            # without a camera stop or direction snap at the loop seam.
            first.handle_left_type = "FREE"
            first.handle_right_type = "FREE"
            last.handle_left_type = "FREE"
            last.handle_right_type = "FREE"
            next_point = min((point for point in curve.keyframe_points if point.co.x > first.co.x), key=lambda item: item.co.x)
            seam_slope = (next_point.co.y - first.co.y) / (next_point.co.x - first.co.x)
            first.handle_left = (first.co.x - 18.0, first.co.y - seam_slope * 18.0)
            first.handle_right = (first.co.x + 18.0, first.co.y + seam_slope * 18.0)
            last.handle_left = (last.co.x - 18.0, last.co.y - seam_slope * 18.0)
            last.handle_right = (last.co.x + 18.0, last.co.y + seam_slope * 18.0)
        curve.update()


def key_camera_path(scene):
    camera = bpy.data.objects.get("VENUS_Hall_Camera")
    target = bpy.data.objects.get("VENUS_Camera_Target")
    if camera is None or target is None:
        raise RuntimeError("The hall camera or its Track To target is missing")
    if not any(constraint.type == "TRACK_TO" and constraint.target == target for constraint in camera.constraints):
        raise RuntimeError("The hall camera no longer tracks VENUS_Camera_Target")

    remove_all_drivers(camera, "location")
    remove_all_drivers(target, "location")
    remove_all_drivers(camera.data, "lens")

    for shot in SHOTS:
        frame = shot["frame"]
        scene.frame_set(frame)
        camera.location = shot["location"]
        target.location = shot["target"]
        camera.data.lens = shot["lens"]
        camera.keyframe_insert(data_path="location", frame=frame, group="Cinematic Camera")
        target.keyframe_insert(data_path="location", frame=frame, group="Cinematic Camera Target")
        camera.data.keyframe_insert(data_path="lens", frame=frame, group="Cinematic Focal Length")

    configure_interpolation(camera, "location", manual_loop_endpoints=True)
    configure_interpolation(target, "location", manual_loop_endpoints=True)
    configure_interpolation(camera.data, "lens", manual_loop_endpoints=True)
    scene.frame_start = 1
    scene.frame_end = 300
    scene.frame_set(1)
    bpy.context.view_layer.update()
    return camera, target


def projected_bounds(scene, camera, obj):
    points = [world_to_camera_view(scene, camera, obj.matrix_world @ Vector(corner)) for corner in obj.bound_box]
    return {
        "x_min": round(min(point.x for point in points), 6),
        "x_max": round(max(point.x for point in points), 6),
        "y_min": round(min(point.y for point in points), 6),
        "y_max": round(max(point.y for point in points), 6),
    }


def frame_state(scene, camera, target, statue, shot):
    scene.frame_set(shot["frame"])
    bpy.context.view_layer.update()
    return {
        "frame": shot["frame"],
        "beat": shot["beat"],
        "camera_location": rounded(camera.matrix_world.translation),
        "target_location": rounded(target.matrix_world.translation),
        "lens_mm": round(float(camera.data.lens), 4),
        "projected_statue_bounds": projected_bounds(scene, camera, statue),
    }


def main():
    scene = bpy.context.scene
    statue = bpy.data.objects.get("VENUS_Hunyuan_Working")
    if statue is None or statue.active_material is None:
        raise RuntimeError("The final Venus mesh or material is missing")
    if statue.active_material.name != "VENUS_Restoration_Material_v9_CleanResin":
        raise RuntimeError(f"Unexpected active material: {statue.active_material.name}")

    hidden = hide_obsolete_assets()
    camera, target = key_camera_path(scene)
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
        "resolution": [1280, 720],
        "fps": 30,
        "engine": scene.render.engine,
        "hidden_obsolete_objects": hidden,
        "states": [],
    }

    for shot in SHOTS:
        state = frame_state(scene, camera, target, statue, shot)
        scene.render.filepath = str(OUTPUT_DIR / f"venus-story-{shot['frame']:03d}.png")
        started = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        state["render_seconds"] = round(time.perf_counter() - started, 3)
        state["output"] = scene.render.filepath
        report["states"].append(state)
        print({"frame": state["frame"], "beat": state["beat"], "bounds": state["projected_statue_bounds"], "seconds": state["render_seconds"]})

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    scene.frame_set(1)
    scene["VENUS_STAGE"] = "cinematic_storyboard"
    scene["VENUS_STORYBOARD_REPORT"] = str(REPORT_PATH)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print({"blend": str(BLEND_PATH), "storyboard": str(OUTPUT_DIR), "report": str(REPORT_PATH), "hidden_obsolete_count": len(hidden)})


try:
    main()
except Exception:
    traceback.print_exc()
    raise
