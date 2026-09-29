"""Refine marble tonality and split repair regions into obsidian, resin, and aged metal."""

from pathlib import Path
import traceback

import bpy
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BLEND_PATH = PROJECT / "blend" / "venus-restoration-v11-material-refined.blend"
OUTPUT_DIR = PROJECT / "renders" / "previews" / "venus-v11-material"
STATUE_NAME = "VENUS_Hunyuan_Working"
REVIEW_COLLECTION = "VENUS_V11_REVIEW"


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def remove_collection(name: str) -> None:
    collection = bpy.data.collections.get(name)
    if collection is None:
        return
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def set_socket(node, name, value) -> None:
    socket = node.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def refine_material(statue: bpy.types.Object) -> bpy.types.Material:
    source = statue.active_material
    if source is None or not source.use_nodes:
        raise RuntimeError("The face-refined material is unavailable")
    material = source.copy()
    material.name = "VENUS_Restoration_Material_v5_Museum"
    statue.data.materials[0] = material
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    output = next(node for node in nodes if node.type == "OUTPUT_MATERIAL")
    texture_nodes = [node for node in nodes if node.type == "TEX_IMAGE"]
    base_texture = next(node for node in texture_nodes if node.image and "normal" not in node.image.name.lower() and "roughness" not in node.image.name.lower())
    repair_mask = next(node for node in nodes if node.type == "VALTORGB" and node.name == "VENUS_RepairRegionMask")
    face_mix = next(node for node in nodes if node.type == "MIX_SHADER" and node.name == "VENUS_MixFacePolish")

    marble_tint = next(node for node in nodes if node.type == "MIX_RGB" and node.label == "VENUS_MarbleTint")
    obsidian_tint = next(node for node in nodes if node.type == "MIX_RGB" and node.label == "VENUS_ObsidianTint")
    resin_tint = next(node for node in nodes if node.type == "MIX_RGB" and node.label == "VENUS_ResinTint")
    marble_tint.inputs[2].default_value = (0.70, 0.73, 0.78, 1.0)
    obsidian_tint.inputs[2].default_value = (0.052, 0.070, 0.095, 1.0)
    resin_tint.inputs[2].default_value = (0.34, 0.16, 0.055, 1.0)

    principled = [node for node in nodes if node.type == "BSDF_PRINCIPLED"]
    marble = next(node for node in principled if node.label == "VENUS_Carrara")
    obsidian = next(node for node in principled if node.label == "VENUS_Obsidian")
    resin = next(node for node in principled if node.label == "VENUS_SmokedResin")
    face = next(node for node in principled if node.label == "VENUS_FacePolishedCarrara")
    set_socket(marble, "Roughness", 0.34)
    set_socket(marble, "Coat Weight", 0.025)
    set_socket(face, "Roughness", 0.30)
    set_socket(face, "Coat Weight", 0.025)
    set_socket(face, "Subsurface Weight", 0.035)
    set_socket(obsidian, "Roughness", 0.18)
    set_socket(obsidian, "Coat Weight", 0.12)
    set_socket(resin, "Roughness", 0.20)
    set_socket(resin, "Transmission Weight", 0.58)
    set_socket(resin, "Coat Weight", 0.06)
    set_socket(resin, "IOR", 1.46)

    to_bw = nodes.new("ShaderNodeRGBToBW")
    to_bw.name = "VENUS_BaseLuminance"
    to_bw.location = (250, -780)
    links.new(base_texture.outputs["Color"], to_bw.inputs["Color"])

    bright_mask = nodes.new("ShaderNodeValToRGB")
    bright_mask.name = "VENUS_AgedMetalBrightnessMask"
    bright_mask.location = (450, -780)
    bright_mask.color_ramp.elements[0].position = 0.43
    bright_mask.color_ramp.elements[0].color = (0, 0, 0, 1)
    bright_mask.color_ramp.elements[1].position = 0.64
    bright_mask.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(to_bw.outputs[0], bright_mask.inputs["Fac"])

    metal_mask = nodes.new("ShaderNodeMath")
    metal_mask.name = "VENUS_AgedMetalMask"
    metal_mask.operation = "MULTIPLY"
    metal_mask.location = (670, -720)
    links.new(repair_mask.outputs["Color"], metal_mask.inputs[0])
    links.new(bright_mask.outputs["Color"], metal_mask.inputs[1])

    aged_metal = nodes.new("ShaderNodeBsdfPrincipled")
    aged_metal.name = "VENUS_AgedMetal"
    aged_metal.label = "VENUS_AgedMetal"
    aged_metal.location = (900, -650)
    set_socket(aged_metal, "Base Color", (0.12, 0.055, 0.024, 1.0))
    set_socket(aged_metal, "Metallic", 0.86)
    set_socket(aged_metal, "Roughness", 0.29)
    set_socket(aged_metal, "Coat Weight", 0.04)

    preface_link = next(link for link in links if link.to_node == face_mix and link.to_socket == face_mix.inputs[1])
    preface_surface = preface_link.from_socket
    links.remove(preface_link)
    metal_mix = nodes.new("ShaderNodeMixShader")
    metal_mix.name = "VENUS_MixAgedMetal"
    metal_mix.location = (1120, -240)
    links.new(metal_mask.outputs[0], metal_mix.inputs[0])
    links.new(preface_surface, metal_mix.inputs[1])
    links.new(aged_metal.outputs["BSDF"], metal_mix.inputs[2])
    links.new(metal_mix.outputs[0], face_mix.inputs[1])

    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    if hasattr(bpy.context.scene.eevee, "use_raytracing"):
        bpy.context.scene.eevee.use_raytracing = True
    return material


def add_face_key() -> bpy.types.Object:
    existing = bpy.data.objects.get("VENUS_Sculpture_Face_Key")
    if existing is not None:
        return existing
    collection = bpy.data.collections.get("VENUS_HALL") or bpy.context.scene.collection
    data = bpy.data.lights.new("VENUS_Sculpture_Face_Key", type="AREA")
    data.energy = 180
    data.shape = "DISK"
    data.size = 0.72
    data.color = (1.0, 0.78, 0.62)
    light = bpy.data.objects.new("VENUS_Sculpture_Face_Key", data)
    collection.objects.link(light)
    light.location = (1.05, -1.85, 3.65)
    look_at(light, Vector((2.15, 0.0, 2.92)))
    return light


def create_review_camera(collection, name, location, lens, target):
    data = bpy.data.cameras.new(name)
    camera = bpy.data.objects.new(name, data)
    collection.objects.link(camera)
    camera.data.lens = lens
    camera.location = location
    look_at(camera, Vector(target))
    return camera


def render_reviews() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(1)
    old_camera = scene.camera
    old_resolution = (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage)
    old_filepath = scene.render.filepath

    remove_collection(REVIEW_COLLECTION)
    collection = bpy.data.collections.new(REVIEW_COLLECTION)
    scene.collection.children.link(collection)
    full = create_review_camera(collection, "VENUS_V11_Full_Camera", (5.85, -6.5, 2.15), 78, (2.15, 0.0, 1.72))
    detail = create_review_camera(collection, "VENUS_V11_Detail_Camera", (4.50, -4.15, 2.72), 92, (2.15, 0.0, 2.35))

    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.camera = full
    scene.render.filepath = str(OUTPUT_DIR / "venus-v11-full.png")
    bpy.ops.render.render(write_still=True)
    scene.camera = detail
    scene.render.filepath = str(OUTPUT_DIR / "venus-v11-detail.png")
    bpy.ops.render.render(write_still=True)

    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.camera = old_camera
    scene.render.filepath = str(OUTPUT_DIR / "venus-v11-hall-001.png")
    bpy.ops.render.render(write_still=True)

    scene.camera = old_camera
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = old_resolution
    scene.render.filepath = old_filepath
    remove_collection(REVIEW_COLLECTION)


def main() -> None:
    statue = bpy.data.objects.get(STATUE_NAME)
    if statue is None or statue.type != "MESH":
        raise RuntimeError(f"Missing mesh: {STATUE_NAME}")
    material = refine_material(statue)
    face_key = add_face_key()
    render_reviews()
    statue["VENUS_MATERIAL_REVISION"] = "v5_museum"
    bpy.context.scene["VENUS_STAGE"] = "material_refined"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print({"blend": str(BLEND_PATH), "material": material.name, "face_key": face_key.name, "review_dir": str(OUTPUT_DIR)})


try:
    main()
except Exception:
    traceback.print_exc()
    raise
