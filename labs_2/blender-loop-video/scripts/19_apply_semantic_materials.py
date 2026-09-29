"""Apply verified base-color semantic masks to the museum Venus material."""

from pathlib import Path
import traceback

import bpy
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BLEND_PATH = PROJECT / "blend" / "venus-restoration-v12-semantic-materials.blend"
OUTPUT_DIR = PROJECT / "renders" / "previews" / "venus-v12-semantic"
STATUE_NAME = "VENUS_Hunyuan_Working"
REVIEW_COLLECTION = "VENUS_V12_REVIEW"


def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def remove_collection(name):
    collection = bpy.data.collections.get(name)
    if collection is None:
        return
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def math_node(nodes, name, operation):
    old = nodes.get(name)
    if old is not None:
        nodes.remove(old)
    node = nodes.new("ShaderNodeMath")
    node.name = name
    node.operation = operation
    return node


def apply_semantic_masks(statue):
    source = statue.active_material
    material = source.copy()
    material.name = "VENUS_Restoration_Material_v6_Semantic"
    statue.data.materials[0] = material
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    luma = nodes.get("VENUS_SemanticLuminance")
    rgb = nodes.get("VENUS_SemanticRGB")
    obsidian = nodes.get("VENUS_SemanticObsidian")
    warm_mask = nodes.get("VENUS_SemanticResinWarm")
    if not all((luma, rgb, obsidian, warm_mask)):
        raise RuntimeError("Run the semantic-mask diagnostic before applying materials")

    obsidian.color_ramp.elements[0].position = 0.06
    obsidian.color_ramp.elements[0].color = (1, 1, 1, 1)
    obsidian.color_ramp.elements[1].position = 0.20
    obsidian.color_ramp.elements[1].color = (0, 0, 0, 1)
    warm_mask.color_ramp.elements[0].position = 0.018
    warm_mask.color_ramp.elements[1].position = 0.11

    not_obsidian = math_node(nodes, "VENUS_SemanticNotObsidianV2", "SUBTRACT")
    not_obsidian.inputs[0].default_value = 1.0
    links.new(obsidian.outputs["Color"], not_obsidian.inputs[1])
    above_dark = math_node(nodes, "VENUS_ResinAboveDark", "GREATER_THAN")
    above_dark.inputs[1].default_value = 0.18
    links.new(luma.outputs[0], above_dark.inputs[0])
    below_marble = math_node(nodes, "VENUS_ResinBelowMarble", "LESS_THAN")
    below_marble.inputs[1].default_value = 0.58
    links.new(luma.outputs[0], below_marble.inputs[0])
    mid_band = math_node(nodes, "VENUS_ResinMidBand", "MULTIPLY")
    links.new(above_dark.outputs[0], mid_band.inputs[0])
    links.new(below_marble.outputs[0], mid_band.inputs[1])
    warm_mid = math_node(nodes, "VENUS_ResinWarmMid", "MULTIPLY")
    links.new(warm_mask.outputs["Color"], warm_mid.inputs[0])
    links.new(mid_band.outputs[0], warm_mid.inputs[1])
    resin = math_node(nodes, "VENUS_SemanticResinV2", "MULTIPLY")
    links.new(warm_mid.outputs[0], resin.inputs[0])
    links.new(not_obsidian.outputs[0], resin.inputs[1])

    obsidian_mix = nodes.get("VENUS_MixMarbleObsidian")
    resin_mix = nodes.get("VENUS_MixResin")
    metal_mix = nodes.get("VENUS_MixAgedMetal")
    if not all((obsidian_mix, resin_mix, metal_mix)):
        raise RuntimeError("Expected material mix nodes are missing")
    for target in (obsidian_mix.inputs[0], resin_mix.inputs[0], metal_mix.inputs[0]):
        for link in list(target.links):
            links.remove(link)
    links.new(obsidian.outputs["Color"], obsidian_mix.inputs[0])
    links.new(resin.outputs[0], resin_mix.inputs[0])
    metal_mix.inputs[0].default_value = 0.0

    resin_tint = next(node for node in nodes if node.type == "MIX_RGB" and node.label == "VENUS_ResinTint")
    resin_tint.inputs[2].default_value = (0.48, 0.22, 0.075, 1.0)
    resin_bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED" and node.label == "VENUS_SmokedResin")
    resin_bsdf.inputs["Roughness"].default_value = 0.24
    resin_bsdf.inputs["Transmission Weight"].default_value = 0.50
    resin_bsdf.inputs["Coat Weight"].default_value = 0.035
    statue["VENUS_SEMANTIC_MASKS"] = "luminance_and_warmth"
    return material


def camera(collection, name, location, lens, target):
    data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    data.lens = lens
    obj.location = location
    look_at(obj, Vector(target))
    return obj


def render_reviews():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(1)
    old_camera = scene.camera
    old_render = (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.filepath)
    remove_collection(REVIEW_COLLECTION)
    collection = bpy.data.collections.new(REVIEW_COLLECTION)
    scene.collection.children.link(collection)
    full = camera(collection, "VENUS_V12_Full", (5.85, -6.5, 2.15), 78, (2.15, 0.0, 1.72))
    detail = camera(collection, "VENUS_V12_Detail", (4.50, -4.15, 2.72), 92, (2.15, 0.0, 2.35))
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    for cam, filename in [(full, "venus-v12-full.png"), (detail, "venus-v12-detail.png")]:
        scene.camera = cam
        scene.render.filepath = str(OUTPUT_DIR / filename)
        bpy.ops.render.render(write_still=True)
    scene.camera = old_camera
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.filepath = str(OUTPUT_DIR / "venus-v12-hall-001.png")
    bpy.ops.render.render(write_still=True)
    scene.camera = old_camera
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.filepath = old_render
    remove_collection(REVIEW_COLLECTION)


def main():
    statue = bpy.data.objects.get(STATUE_NAME)
    if statue is None or statue.type != "MESH":
        raise RuntimeError(f"Missing mesh: {STATUE_NAME}")
    material = apply_semantic_masks(statue)
    render_reviews()
    bpy.context.scene["VENUS_STAGE"] = "semantic_materials"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print({"blend": str(BLEND_PATH), "material": material.name, "review_dir": str(OUTPUT_DIR)})


try:
    main()
except Exception:
    traceback.print_exc()
    raise
