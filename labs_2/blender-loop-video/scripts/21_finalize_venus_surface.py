"""Finalize smoked-resin surface without changing the verified face and masks."""

from pathlib import Path
import traceback

import bpy
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BLEND_PATH = PROJECT / "blend" / "venus-restoration-v14-final-surface.blend"
OUTPUT_DIR = PROJECT / "renders" / "previews" / "venus-v14-final"
STATUE = "VENUS_Hunyuan_Working"
COLLECTION = "VENUS_V14_REVIEW"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def clear_collection(name):
    col = bpy.data.collections.get(name)
    if col:
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)


def make_camera(col, name, location, lens, target):
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
    material = statue.active_material.copy()
    material.name = "VENUS_Restoration_Material_v8_Final"
    statue.data.materials[0] = material
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    resin = next(node for node in nodes if node.type == "BSDF_PRINCIPLED" and node.label == "VENUS_SmokedResin")
    for link in list(resin.inputs["Normal"].links):
        links.remove(link)
    source_normal = next(node for node in nodes if node.type == "NORMAL_MAP" and node.name == "VENUS_SourceNormal")
    source_link = next(link for link in links if link.to_node == source_normal and link.to_socket == source_normal.inputs["Color"])
    resin_normal = nodes.new("ShaderNodeNormalMap")
    resin_normal.name = "VENUS_ResinFineNormal"
    resin_normal.inputs["Strength"].default_value = 0.07
    links.new(source_link.from_socket, resin_normal.inputs["Color"])
    links.new(resin_normal.outputs["Normal"], resin.inputs["Normal"])
    resin.inputs["Roughness"].default_value = 0.30
    resin.inputs["Transmission Weight"].default_value = 0.27
    resin.inputs["Coat Weight"].default_value = 0.015
    tint = next(node for node in nodes if node.type == "MIX_RGB" and node.label == "VENUS_ResinTint")
    tint.inputs[2].default_value = (0.145, 0.065, 0.038, 1.0)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(1)
    old_camera = scene.camera
    old_render = (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.filepath)
    clear_collection(COLLECTION)
    col = bpy.data.collections.new(COLLECTION)
    scene.collection.children.link(col)
    full = make_camera(col, "VENUS_V14_Full", (5.85, -6.5, 2.15), 78, (2.15, 0, 1.72))
    detail = make_camera(col, "VENUS_V14_Detail", (4.5, -4.15, 2.72), 92, (2.15, 0, 2.35))
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    for camera, filename in [(full, "venus-v14-full.png"), (detail, "venus-v14-detail.png")]:
        scene.camera = camera
        scene.render.filepath = str(OUTPUT_DIR / filename)
        bpy.ops.render.render(write_still=True)
    scene.camera = old_camera
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.filepath = str(OUTPUT_DIR / "venus-v14-hall-001.png")
    bpy.ops.render.render(write_still=True)
    scene.camera = old_camera
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.filepath = old_render
    clear_collection(COLLECTION)
    statue["VENUS_SURFACE_REVISION"] = "final_low_frequency_resin_normal"
    scene["VENUS_STAGE"] = "final_surface"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print({"blend": str(BLEND_PATH), "material": material.name, "review": str(OUTPUT_DIR)})


try:
    main()
except Exception:
    traceback.print_exc()
    raise
