"""Render controlled face comparisons to isolate mesh, normal, and bump roughness."""

from pathlib import Path
import traceback

import bpy
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
OUTPUT_DIR = PROJECT / "renders" / "previews" / "face-diagnostics"
STATUE_NAME = "VENUS_Hunyuan_Working"
DIAGNOSTIC_COLLECTION = "VENUS_FACE_DIAGNOSTICS"


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def remove_collection(name: str) -> None:
    collection = bpy.data.collections.get(name)
    if collection is None:
        return
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def add_area_light(collection, name, location, energy, size, color, target):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    light = bpy.data.objects.new(name, data)
    collection.objects.link(light)
    light.location = location
    look_at(light, target)
    return light


def make_neutral_material() -> bpy.types.Material:
    material = bpy.data.materials.get("VENUS_Diagnostic_Neutral") or bpy.data.materials.new(
        "VENUS_Diagnostic_Neutral"
    )
    material.use_nodes = True
    nodes = material.node_tree.nodes
    principled = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    principled.inputs["Base Color"].default_value = (0.52, 0.54, 0.57, 1.0)
    principled.inputs["Metallic"].default_value = 0.0
    principled.inputs["Roughness"].default_value = 0.42
    return material


def render(path: Path) -> None:
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    statue = bpy.data.objects.get(STATUE_NAME)
    if statue is None or statue.type != "MESH":
        raise RuntimeError(f"Missing mesh: {STATUE_NAME}")
    material = statue.active_material
    if material is None or not material.use_nodes:
        raise RuntimeError("The statue material is unavailable")

    normal = next((node for node in material.node_tree.nodes if node.type == "NORMAL_MAP"), None)
    bump = next((node for node in material.node_tree.nodes if node.type == "BUMP"), None)
    if normal is None or bump is None:
        raise RuntimeError("Expected normal-map and bump nodes were not found")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    old_camera = scene.camera
    old_resolution = (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage)
    old_filepath = scene.render.filepath
    old_normal_strength = normal.inputs["Strength"].default_value
    old_bump_strength = bump.inputs["Strength"].default_value
    old_materials = list(statue.data.materials)

    remove_collection(DIAGNOSTIC_COLLECTION)
    collection = bpy.data.collections.new(DIAGNOSTIC_COLLECTION)
    scene.collection.children.link(collection)

    camera_data = bpy.data.cameras.new("VENUS_Face_Diagnostic_Camera")
    camera = bpy.data.objects.new("VENUS_Face_Diagnostic_Camera", camera_data)
    collection.objects.link(camera)
    camera.data.lens = 88
    camera.location = (2.15, -2.15, 2.86)
    look_at(camera, Vector((2.15, 0.0, 2.78)))
    scene.camera = camera

    target = Vector((2.15, 0.0, 2.76))
    add_area_light(collection, "VENUS_Diag_Key", (0.75, -1.25, 3.55), 820, 1.35, (1.0, 0.88, 0.76), target)
    add_area_light(collection, "VENUS_Diag_Fill", (3.25, -0.75, 3.05), 420, 1.15, (0.68, 0.80, 1.0), target)
    add_area_light(collection, "VENUS_Diag_Rim", (2.55, 0.70, 3.35), 650, 0.9, (0.54, 0.70, 1.0), target)

    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100

    render(OUTPUT_DIR / "01-current.png")

    bump.inputs["Strength"].default_value = 0.0
    render(OUTPUT_DIR / "02-no-micro-bump.png")

    normal.inputs["Strength"].default_value = 0.0
    render(OUTPUT_DIR / "03-no-normal-map.png")

    neutral = make_neutral_material()
    statue.data.materials.clear()
    statue.data.materials.append(neutral)
    render(OUTPUT_DIR / "04-geometry-only.png")

    statue.data.materials.clear()
    for old_material in old_materials:
        statue.data.materials.append(old_material)
    normal.inputs["Strength"].default_value = old_normal_strength
    bump.inputs["Strength"].default_value = old_bump_strength
    scene.camera = old_camera
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = old_resolution
    scene.render.filepath = old_filepath
    remove_collection(DIAGNOSTIC_COLLECTION)
    print(
        {
            "output": str(OUTPUT_DIR),
            "normal_strength": old_normal_strength,
            "micro_bump_strength": old_bump_strength,
            "status": "restored",
        }
    )


try:
    main()
except Exception:
    traceback.print_exc()
    raise
