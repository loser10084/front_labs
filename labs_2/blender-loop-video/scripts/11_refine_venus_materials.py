"""Rebuild the Hunyuan statue material into marble, obsidian, resin, and metal."""

from pathlib import Path
import traceback

import bpy
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BLEND_PATH = PROJECT / "blend" / "venus-restoration-v06-lookdev.blend"
PREVIEW_DIR = PROJECT / "renders" / "previews" / "venus-lookdev"


def socket(node, name: str, fallback_index: int):
    return node.inputs.get(name) or node.inputs[fallback_index]


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def tint_node(nodes, links, name, source, tint):
    node = nodes.new("ShaderNodeMixRGB")
    node.name = name
    node.label = name
    node.blend_type = "MULTIPLY"
    node.inputs[0].default_value = 1.0
    node.inputs[2].default_value = tint
    links.new(source, node.inputs[1])
    return node


def make_principled(nodes, name, base_output, roughness, metallic=0.0, transmission=0.0, coat=0.0):
    node = nodes.new("ShaderNodeBsdfPrincipled")
    node.name = name
    node.label = name
    socket(node, "Roughness", 2).default_value = roughness
    socket(node, "Metallic", 1).default_value = metallic
    socket(node, "Transmission Weight", 17).default_value = transmission
    socket(node, "Coat Weight", 18).default_value = coat
    socket(node, "Coat Roughness", 19).default_value = 0.08 if coat else 0.03
    return node


def build_material(statue: bpy.types.Object) -> bpy.types.Material:
    source_material = statue.data.materials[0]
    source_material.name = "VENUS_Source_PBR"
    base_image = bpy.data.images.get("texture_pbr_20250901")
    normal_image = bpy.data.images.get("texture_pbr_20250901_normal")
    packed_image = bpy.data.images.get("texture_pbr_20250901_metallic-texture_pbr_20250901_roughness")
    if base_image is None or normal_image is None or packed_image is None:
        raise RuntimeError("Expected Hunyuan base-color, packed metallic/roughness, and normal images were not found")

    material = bpy.data.materials.get("VENUS_Restoration_Material_v3") or bpy.data.materials.new(
        "VENUS_Restoration_Material_v3"
    )
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.name = "VENUS_Output"
    output.location = (980, 80)

    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-1100, 0)

    base_tex = nodes.new("ShaderNodeTexImage")
    base_tex.name = "VENUS_BaseColor_4K"
    base_tex.image = base_image
    base_tex.location = (-900, 160)
    links.new(texcoord.outputs["UV"], base_tex.inputs["Vector"])

    normal_tex = nodes.new("ShaderNodeTexImage")
    normal_tex.name = "VENUS_Normal_4K"
    normal_tex.image = normal_image
    normal_tex.image.colorspace_settings.name = "Non-Color"
    normal_tex.location = (-900, -500)
    links.new(texcoord.outputs["UV"], normal_tex.inputs["Vector"])

    packed_tex = nodes.new("ShaderNodeTexImage")
    packed_tex.name = "VENUS_MetallicRoughness_4K"
    packed_tex.image = packed_image
    packed_tex.image.colorspace_settings.name = "Non-Color"
    packed_tex.location = (-900, -180)
    links.new(texcoord.outputs["UV"], packed_tex.inputs["Vector"])

    packed_channels = nodes.new("ShaderNodeSeparateColor")
    packed_channels.name = "VENUS_PackedChannels"
    packed_channels.mode = "RGB"
    packed_channels.location = (-650, -180)
    links.new(packed_tex.outputs["Color"], packed_channels.inputs["Color"])

    repair_mask = nodes.new("ShaderNodeValToRGB")
    repair_mask.name = "VENUS_RepairRegionMask"
    repair_mask.color_ramp.interpolation = "EASE"
    repair_mask.color_ramp.elements[0].position = 0.22
    repair_mask.color_ramp.elements[0].color = (0, 0, 0, 1)
    repair_mask.color_ramp.elements[1].position = 0.68
    repair_mask.color_ramp.elements[1].color = (1, 1, 1, 1)
    repair_mask.location = (-400, -220)
    links.new(packed_channels.outputs["Blue"], repair_mask.inputs["Fac"])

    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.name = "VENUS_SourceNormal"
    normal_map.inputs["Strength"].default_value = 0.72
    normal_map.location = (-650, -500)
    links.new(normal_tex.outputs["Color"], normal_map.inputs["Color"])

    noise = nodes.new("ShaderNodeTexNoise")
    noise.name = "VENUS_MicroSurface"
    noise.noise_dimensions = "3D"
    noise.inputs["Scale"].default_value = 260.0
    noise.inputs["Detail"].default_value = 1.8
    noise.inputs["Roughness"].default_value = 0.58
    noise.location = (-650, -700)
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])

    bump = nodes.new("ShaderNodeBump")
    bump.name = "VENUS_MicroBump"
    bump.inputs["Strength"].default_value = 0.012
    bump.inputs["Distance"].default_value = 0.0002
    bump.location = (-380, -500)
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(normal_map.outputs["Normal"], bump.inputs["Normal"])

    hsv = nodes.new("ShaderNodeSeparateColor")
    hsv.name = "VENUS_MaterialClassifier"
    hsv.mode = "HSV"
    hsv.location = (-650, 120)
    links.new(base_tex.outputs["Color"], hsv.inputs["Color"])

    black_mask = nodes.new("ShaderNodeValToRGB")
    black_mask.name = "VENUS_ObsidianMask"
    black_mask.color_ramp.interpolation = "EASE"
    black_mask.color_ramp.elements[0].position = 0.20
    black_mask.color_ramp.elements[0].color = (1, 1, 1, 1)
    black_mask.color_ramp.elements[1].position = 0.43
    black_mask.color_ramp.elements[1].color = (0, 0, 0, 1)
    black_mask.location = (-400, 220)
    links.new(hsv.outputs["Blue"], black_mask.inputs["Fac"])

    invert_black = nodes.new("ShaderNodeMath")
    invert_black.name = "VENUS_NotObsidian"
    invert_black.operation = "SUBTRACT"
    invert_black.inputs[0].default_value = 1.0
    invert_black.location = (-160, 130)
    links.new(black_mask.outputs["Color"], invert_black.inputs[1])

    obsidian_mask = nodes.new("ShaderNodeMath")
    obsidian_mask.name = "VENUS_ObsidianInRepairRegions"
    obsidian_mask.operation = "MULTIPLY"
    obsidian_mask.location = (20, 170)
    links.new(repair_mask.outputs["Color"], obsidian_mask.inputs[0])
    links.new(black_mask.outputs["Color"], obsidian_mask.inputs[1])

    resin_mask = nodes.new("ShaderNodeMath")
    resin_mask.name = "VENUS_ResinMask"
    resin_mask.operation = "MULTIPLY"
    resin_mask.location = (20, -10)
    links.new(repair_mask.outputs["Color"], resin_mask.inputs[0])
    links.new(invert_black.outputs[0], resin_mask.inputs[1])

    marble_tint = tint_node(nodes, links, "VENUS_MarbleTint", base_tex.outputs["Color"], (0.92, 0.94, 0.97, 1))
    marble_tint.location = (-140, 520)
    obsidian_tint = tint_node(nodes, links, "VENUS_ObsidianTint", base_tex.outputs["Color"], (0.12, 0.16, 0.22, 1))
    obsidian_tint.location = (-140, 390)
    resin_tint = tint_node(nodes, links, "VENUS_ResinTint", base_tex.outputs["Color"], (0.78, 0.42, 0.16, 1))
    resin_tint.location = (-140, 260)

    marble = make_principled(nodes, "VENUS_Carrara", marble_tint.outputs["Color"], 0.34, coat=0.08)
    marble.location = (160, 520)
    marble.inputs["Subsurface Weight"].default_value = 0.035
    marble.inputs["Subsurface Scale"].default_value = 0.012
    links.new(marble_tint.outputs["Color"], marble.inputs["Base Color"])
    links.new(bump.outputs["Normal"], marble.inputs["Normal"])

    obsidian = make_principled(nodes, "VENUS_Obsidian", obsidian_tint.outputs["Color"], 0.22, coat=0.18)
    obsidian.location = (160, 340)
    obsidian.inputs["IOR"].default_value = 1.52
    links.new(obsidian_tint.outputs["Color"], obsidian.inputs["Base Color"])
    links.new(bump.outputs["Normal"], obsidian.inputs["Normal"])

    resin = make_principled(nodes, "VENUS_SmokedResin", resin_tint.outputs["Color"], 0.22, transmission=0.42, coat=0.18)
    resin.location = (160, 150)
    resin.inputs["IOR"].default_value = 1.46
    resin.inputs["Emission Color"].default_value = (0.20, 0.045, 0.008, 1)
    resin.inputs["Emission Strength"].default_value = 0.025
    links.new(resin_tint.outputs["Color"], resin.inputs["Base Color"])
    links.new(bump.outputs["Normal"], resin.inputs["Normal"])

    mix_stone = nodes.new("ShaderNodeMixShader")
    mix_stone.name = "VENUS_MixMarbleObsidian"
    mix_stone.location = (500, 410)
    links.new(obsidian_mask.outputs[0], mix_stone.inputs[0])
    links.new(marble.outputs["BSDF"], mix_stone.inputs[1])
    links.new(obsidian.outputs["BSDF"], mix_stone.inputs[2])

    mix_resin = nodes.new("ShaderNodeMixShader")
    mix_resin.name = "VENUS_MixResin"
    mix_resin.location = (730, 260)
    links.new(resin_mask.outputs[0], mix_resin.inputs[0])
    links.new(mix_stone.outputs[0], mix_resin.inputs[1])
    links.new(resin.outputs["BSDF"], mix_resin.inputs[2])
    links.new(mix_resin.outputs[0], output.inputs["Surface"])

    statue.data.materials.clear()
    statue.data.materials.append(material)
    statue["VENUS_MATERIAL_RATIO"] = "marble40_obsidian30_resin20_metal10"
    statue["VENUS_STAGE"] = "lookdev_v3"
    return material


def render_views() -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    camera = bpy.data.objects.get("VENUS_Inspection_Camera")
    if camera is None:
        raise RuntimeError("Inspection camera is missing")
    target = Vector((0, 0, 1.72))
    views = {
        "front": Vector((0, -6.7, 1.74)),
        "right": Vector((6.7, 0, 1.74)),
        "back": Vector((0, 6.7, 1.74)),
        "left": Vector((-6.7, 0, 1.74)),
    }
    for label, location in views.items():
        camera.location = location
        look_at(camera, target)
        scene.render.filepath = str(PREVIEW_DIR / f"lookdev-{label}.png")
        bpy.ops.render.render(write_still=True)


def main() -> None:
    statue = bpy.data.objects.get("VENUS_Hunyuan_Working")
    if statue is None or statue.type != "MESH":
        raise RuntimeError("Prepared Venus mesh is missing")
    material = build_material(statue)
    render_views()
    bpy.context.scene["VENUS_STAGE"] = "lookdev_v3_rendered"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print({"blend": str(BLEND_PATH), "material": material.name, "preview_dir": str(PREVIEW_DIR)})


try:
    main()
except Exception:
    traceback.print_exc()
    raise
