"""Render GPU-evaluated semantic masks without changing the visible statue material."""

from pathlib import Path
import traceback

import bpy
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
OUTPUT_DIR = PROJECT / "renders" / "previews" / "venus-v11-material" / "semantic-masks"
STATUE_NAME = "VENUS_Hunyuan_Working"


def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def new_math(nodes, name, operation):
    node = nodes.new("ShaderNodeMath")
    node.name = name
    node.operation = operation
    return node


def build_masks(material):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    for name in [
        "VENUS_SemanticLuminance",
        "VENUS_SemanticRGB",
        "VENUS_SemanticObsidian",
        "VENUS_SemanticWarmth",
        "VENUS_SemanticResinWarm",
        "VENUS_SemanticNotObsidian",
        "VENUS_SemanticResin",
    ]:
        node = nodes.get(name)
        if node is not None:
            nodes.remove(node)

    images = [node for node in nodes if node.type == "TEX_IMAGE"]
    base = next(node for node in images if node.image and "normal" not in node.image.name.lower() and "roughness" not in node.image.name.lower())

    luma = nodes.new("ShaderNodeRGBToBW")
    luma.name = "VENUS_SemanticLuminance"
    links.new(base.outputs["Color"], luma.inputs["Color"])

    rgb = nodes.new("ShaderNodeSeparateColor")
    rgb.name = "VENUS_SemanticRGB"
    links.new(base.outputs["Color"], rgb.inputs["Color"])

    obsidian = nodes.new("ShaderNodeValToRGB")
    obsidian.name = "VENUS_SemanticObsidian"
    obsidian.color_ramp.elements[0].position = 0.14
    obsidian.color_ramp.elements[0].color = (1, 1, 1, 1)
    obsidian.color_ramp.elements[1].position = 0.34
    obsidian.color_ramp.elements[1].color = (0, 0, 0, 1)
    links.new(luma.outputs[0], obsidian.inputs["Fac"])

    warmth = new_math(nodes, "VENUS_SemanticWarmth", "SUBTRACT")
    warmth.use_clamp = True
    links.new(rgb.outputs["Red"], warmth.inputs[0])
    links.new(rgb.outputs["Blue"], warmth.inputs[1])

    warm_mask = nodes.new("ShaderNodeValToRGB")
    warm_mask.name = "VENUS_SemanticResinWarm"
    warm_mask.color_ramp.elements[0].position = 0.012
    warm_mask.color_ramp.elements[0].color = (0, 0, 0, 1)
    warm_mask.color_ramp.elements[1].position = 0.095
    warm_mask.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(warmth.outputs[0], warm_mask.inputs["Fac"])

    not_obsidian = new_math(nodes, "VENUS_SemanticNotObsidian", "SUBTRACT")
    not_obsidian.inputs[0].default_value = 1.0
    links.new(obsidian.outputs["Color"], not_obsidian.inputs[1])
    resin = new_math(nodes, "VENUS_SemanticResin", "MULTIPLY")
    links.new(warm_mask.outputs["Color"], resin.inputs[0])
    links.new(not_obsidian.outputs[0], resin.inputs[1])
    return luma.outputs[0], obsidian.outputs["Color"], warmth.outputs[0], resin.outputs[0]


def render_masks(statue, outputs):
    scene = bpy.context.scene
    material = statue.active_material
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    output = next(node for node in nodes if node.type == "OUTPUT_MATERIAL")
    surface_link = next(link for link in links if link.to_node == output and link.to_socket == output.inputs["Surface"])
    surface_socket = surface_link.from_socket
    links.remove(surface_link)
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 1.0
    links.new(emission.outputs["Emission"], output.inputs["Surface"])

    packed = nodes.get("VENUS_PackedChannels")
    if packed is None:
        raise RuntimeError("Packed channel node is missing")
    named_outputs = [
        ("01-luminance.png", outputs[0]),
        ("02-obsidian.png", outputs[1]),
        ("03-warmth.png", outputs[2]),
        ("04-resin.png", outputs[3]),
        ("05-packed-blue-raw.png", packed.outputs["Blue"]),
    ]

    old_hide = {obj: obj.hide_render for obj in scene.objects}
    for obj in scene.objects:
        obj.hide_render = obj != statue
    old_transparent = scene.render.film_transparent
    old_camera = scene.camera
    old_render = (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.filepath)
    scene.render.film_transparent = True

    camera_data = bpy.data.cameras.new("VENUS_SemanticMask_Camera")
    camera = bpy.data.objects.new("VENUS_SemanticMask_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.data.lens = 78
    camera.location = (5.85, -6.5, 2.15)
    look_at(camera, Vector((2.15, 0.0, 1.72)))
    scene.camera = camera
    scene.render.resolution_x = 480
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, socket in named_outputs:
        links.new(socket, emission.inputs["Color"])
        scene.render.filepath = str(OUTPUT_DIR / filename)
        bpy.ops.render.render(write_still=True)
        color_link = next(link for link in links if link.to_node == emission and link.to_socket == emission.inputs["Color"])
        links.remove(color_link)

    links.remove(next(link for link in links if link.to_node == output and link.to_socket == output.inputs["Surface"]))
    nodes.remove(emission)
    links.new(surface_socket, output.inputs["Surface"])
    for obj, hidden in old_hide.items():
        obj.hide_render = hidden
    scene.render.film_transparent = old_transparent
    scene.camera = old_camera
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.filepath = old_render
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)


def main():
    statue = bpy.data.objects.get(STATUE_NAME)
    if statue is None or statue.type != "MESH":
        raise RuntimeError(f"Missing mesh: {STATUE_NAME}")
    outputs = build_masks(statue.active_material)
    render_masks(statue, outputs)
    print({"semantic_masks": str(OUTPUT_DIR), "visible_material": "unchanged"})


try:
    main()
except Exception:
    traceback.print_exc()
    raise
