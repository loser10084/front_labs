"""Remove scanned stone albedo from resin regions and save the final clean surface."""

from pathlib import Path
import traceback

import bpy
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BLEND_PATH = PROJECT / "blend" / "venus-restoration-v15-clean-resin.blend"
OUTPUT_DIR = PROJECT / "renders" / "previews" / "venus-v15-clean"
STATUE = "VENUS_Hunyuan_Working"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_review(scene, location, lens, target, resolution, path):
    old_camera = scene.camera
    old_render = (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.filepath)
    data = bpy.data.cameras.new("VENUS_V15_Temporary_Camera")
    camera = bpy.data.objects.new("VENUS_V15_Temporary_Camera", data)
    scene.collection.objects.link(camera)
    camera.location = location
    data.lens = lens
    look_at(camera, target)
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    scene.camera = old_camera
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.filepath = old_render
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(data)


def main():
    statue = bpy.data.objects.get(STATUE)
    if statue is None:
        raise RuntimeError(f"Missing {STATUE}")
    material = statue.active_material.copy()
    material.name = "VENUS_Restoration_Material_v9_CleanResin"
    statue.data.materials[0] = material
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    resin = next(node for node in nodes if node.type == "BSDF_PRINCIPLED" and node.label == "VENUS_SmokedResin")
    for link in list(resin.inputs["Base Color"].links):
        links.remove(link)
    resin.inputs["Base Color"].default_value = (0.105, 0.038, 0.014, 1.0)
    resin.inputs["Roughness"].default_value = 0.29
    resin.inputs["Transmission Weight"].default_value = 0.31
    resin.inputs["Coat Weight"].default_value = 0.012

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(1)
    render_review(scene, (5.85, -6.5, 2.15), 78, (2.15, 0, 1.72), (720, 960), OUTPUT_DIR / "venus-v15-full.png")
    render_review(scene, (4.5, -4.15, 2.72), 92, (2.15, 0, 2.35), (720, 960), OUTPUT_DIR / "venus-v15-detail.png")
    old_camera = scene.camera
    old_render = (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.filepath)
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OUTPUT_DIR / "venus-v15-hall-001.png")
    bpy.ops.render.render(write_still=True)
    scene.camera = old_camera
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.filepath = old_render
    statue["VENUS_SURFACE_REVISION"] = "clean_uniform_smoked_resin"
    scene["VENUS_STAGE"] = "clean_resin_final"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print({"blend": str(BLEND_PATH), "material": material.name, "review": str(OUTPUT_DIR)})


try:
    main()
except Exception:
    traceback.print_exc()
    raise
