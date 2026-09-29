"""Narrow semantic masks for restrained smoked resin and true dark obsidian."""

from pathlib import Path
import traceback

import bpy
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BLEND_PATH = PROJECT / "blend" / "venus-restoration-v13-restrained-materials.blend"
OUTPUT_DIR = PROJECT / "renders" / "previews" / "venus-v13-restrained"
STATUE = "VENUS_Hunyuan_Working"
COLLECTION = "VENUS_V13_REVIEW"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def clear_collection(name):
    col = bpy.data.collections.get(name)
    if col:
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)


def review_camera(col, name, location, lens, target):
    data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, data)
    col.objects.link(obj)
    obj.location = location
    data.lens = lens
    look_at(obj, target)
    return obj


def main():
    statue = bpy.data.objects.get(STATUE)
    if statue is None:
        raise RuntimeError(f"Missing {STATUE}")
    source = statue.active_material
    material = source.copy()
    material.name = "VENUS_Restoration_Material_v7_Restrained"
    statue.data.materials[0] = material
    nodes = material.node_tree.nodes

    obsidian = nodes["VENUS_SemanticObsidian"]
    obsidian.color_ramp.elements[0].position = 0.015
    obsidian.color_ramp.elements[1].position = 0.075
    nodes["VENUS_ResinAboveDark"].inputs[1].default_value = 0.075
    nodes["VENUS_ResinBelowMarble"].inputs[1].default_value = 0.23
    warm = nodes["VENUS_SemanticResinWarm"]
    warm.color_ramp.elements[0].position = 0.035
    warm.color_ramp.elements[1].position = 0.13

    resin_tint = next(node for node in nodes if node.type == "MIX_RGB" and node.label == "VENUS_ResinTint")
    resin_tint.inputs[2].default_value = (0.20, 0.085, 0.038, 1.0)
    resin = next(node for node in nodes if node.type == "BSDF_PRINCIPLED" and node.label == "VENUS_SmokedResin")
    resin.inputs["Roughness"].default_value = 0.32
    resin.inputs["Transmission Weight"].default_value = 0.22
    resin.inputs["Coat Weight"].default_value = 0.02

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(1)
    old_camera = scene.camera
    old_render = (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.filepath)
    clear_collection(COLLECTION)
    col = bpy.data.collections.new(COLLECTION)
    scene.collection.children.link(col)
    full = review_camera(col, "VENUS_V13_Full", (5.85, -6.5, 2.15), 78, (2.15, 0, 1.72))
    detail = review_camera(col, "VENUS_V13_Detail", (4.5, -4.15, 2.72), 92, (2.15, 0, 2.35))
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    for camera, filename in [(full, "venus-v13-full.png"), (detail, "venus-v13-detail.png")]:
        scene.camera = camera
        scene.render.filepath = str(OUTPUT_DIR / filename)
        bpy.ops.render.render(write_still=True)
    scene.camera = old_camera
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.filepath = str(OUTPUT_DIR / "venus-v13-hall-001.png")
    bpy.ops.render.render(write_still=True)
    scene.camera = old_camera
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.filepath = old_render
    clear_collection(COLLECTION)
    statue["VENUS_SEMANTIC_MASKS"] = "restrained_linear_thresholds"
    scene["VENUS_STAGE"] = "restrained_materials"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print({"blend": str(BLEND_PATH), "material": material.name, "review": str(OUTPUT_DIR)})


try:
    main()
except Exception:
    traceback.print_exc()
    raise
