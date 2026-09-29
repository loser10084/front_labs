"""Check storyboard keyframes and camera velocity around the 10-second seam."""

import json

import bpy
from mathutils import Vector


def sample(scene, camera, target, frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    return {
        "camera": camera.matrix_world.translation.copy(),
        "target": target.matrix_world.translation.copy(),
        "lens": float(camera.data.lens),
    }


def vector(value):
    return [round(float(component), 6) for component in value]


scene = bpy.context.scene
camera = bpy.data.objects["VENUS_Hall_Camera"]
target = bpy.data.objects["VENUS_Camera_Target"]
samples = {frame: sample(scene, camera, target, frame) for frame in (1, 2, 76, 151, 226, 300, 301)}

camera_start_velocity = samples[2]["camera"] - samples[1]["camera"]
camera_end_velocity = samples[301]["camera"] - samples[300]["camera"]
target_start_velocity = samples[2]["target"] - samples[1]["target"]
target_end_velocity = samples[301]["target"] - samples[300]["target"]
report = {
    "blend": bpy.data.filepath,
    "sample_frames": [1, 2, 76, 151, 226, 300, 301],
    "camera_endpoint_equal": (samples[1]["camera"] - samples[301]["camera"]).length < 1e-6,
    "target_endpoint_equal": (samples[1]["target"] - samples[301]["target"]).length < 1e-6,
    "lens_endpoint_equal": abs(samples[1]["lens"] - samples[301]["lens"]) < 1e-6,
    "camera_velocity_start": vector(camera_start_velocity),
    "camera_velocity_across_seam": vector(camera_end_velocity),
    "camera_velocity_delta": round(float((camera_end_velocity - camera_start_velocity).length), 6),
    "target_velocity_start": vector(target_start_velocity),
    "target_velocity_across_seam": vector(target_end_velocity),
    "target_velocity_delta": round(float((target_end_velocity - target_start_velocity).length), 6),
    "lens_velocity_start": round(samples[2]["lens"] - samples[1]["lens"], 6),
    "lens_velocity_across_seam": round(samples[301]["lens"] - samples[300]["lens"], 6),
    "shots": {
        str(frame): {
            "camera": vector(samples[frame]["camera"]),
            "target": vector(samples[frame]["target"]),
            "lens_mm": round(samples[frame]["lens"], 4),
        }
        for frame in (1, 76, 151, 226, 301)
    },
}
print(json.dumps(report, ensure_ascii=False, indent=2))
