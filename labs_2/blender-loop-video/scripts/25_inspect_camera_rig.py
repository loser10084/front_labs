"""Inspect the final gate camera rig before choreographing a more legible move."""

import json

import bpy
from mathutils import Vector


scene = bpy.context.scene
camera = scene.camera
statue = bpy.data.objects.get("VENUS_Hunyuan_Working")


def vec(values):
    return [round(float(value), 6) for value in values]


def drivers(owner):
    result = []
    if owner is None or owner.animation_data is None:
        return result
    for curve in owner.animation_data.drivers:
        result.append(
            {
                "path": curve.data_path,
                "index": curve.array_index,
                "expression": curve.driver.expression,
            }
        )
    return result


def describe(obj):
    if obj is None:
        return None
    result = {
        "name": obj.name,
        "type": obj.type,
        "location": vec(obj.location),
        "world_location": vec(obj.matrix_world.translation),
        "rotation": vec(obj.rotation_euler),
        "drivers": drivers(obj),
        "constraints": [],
    }
    for constraint in obj.constraints:
        result["constraints"].append(
            {
                "name": constraint.name,
                "type": constraint.type,
                "target": getattr(getattr(constraint, "target", None), "name", None),
                "track_axis": getattr(constraint, "track_axis", None),
                "up_axis": getattr(constraint, "up_axis", None),
            }
        )
    return result


data = {
    "filepath": bpy.data.filepath,
    "frame": scene.frame_current,
    "frame_range": [scene.frame_start, scene.frame_end],
    "camera": describe(camera),
    "camera_lens": camera.data.lens if camera else None,
    "camera_data_drivers": drivers(camera.data) if camera else [],
    "target": describe(bpy.data.objects.get("VENUS_Camera_Target")),
    "statue": describe(statue),
    "statue_material": statue.active_material.name if statue and statue.active_material else None,
}
if statue:
    points = [statue.matrix_world @ Vector(corner) for corner in statue.bound_box]
    data["statue_bounds"] = {
        "min": [min(point[i] for point in points) for i in range(3)],
        "max": [max(point[i] for point in points) for i in range(3)],
    }
print(json.dumps(data, ensure_ascii=False, indent=2))
