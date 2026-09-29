"""Create a non-destructive face-polish pass and render a close review."""

from pathlib import Path
import traceback

import bpy
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BLEND_PATH = PROJECT / "blend" / "venus-restoration-v10-face-refined.blend"
OUTPUT_DIR = PROJECT / "renders" / "previews" / "venus-v10-face"
STATUE_NAME = "VENUS_Hunyuan_Working"
REVIEW_COLLECTION = "VENUS_FACE_REVIEW"


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def remove_collection(name: str) -> None:
    collection = bpy.data.collections.get(name)
    if collection is None:
        return
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def set_principled(node, *, roughness, ior, coat, subsurface):
    node.inputs["Metallic"].default_value = 0.0
    node.inputs["Roughness"].default_value = roughness
    node.inputs["IOR"].default_value = ior
    node.inputs["Coat Weight"].default_value = coat
    node.inputs["Subsurface Weight"].default_value = subsurface


def refine_face_material(statue: bpy.types.Object) -> bpy.types.Material:
    source = statue.active_material
    if source is None or not source.use_nodes:
        raise RuntimeError("The statue material is unavailable")

    material = source.copy()
    material.name = "VENUS_Restoration_Material_v4_FacePolish"
    statue.data.materials[0] = material
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    output = next(node for node in nodes if node.type == "OUTPUT_MATERIAL")
    texcoord = next(node for node in nodes if node.type == "TEX_COORD")
    source_normal = next(node for node in nodes if node.type == "NORMAL_MAP")
    bump = next(node for node in nodes if node.type == "BUMP")
    marble = next(
        node
        for node in nodes
        if node.type == "BSDF_PRINCIPLED" and node.label == "VENUS_Carrara"
    )

    source_normal.inputs["Strength"].default_value = 0.38
    bump.inputs["Strength"].default_value = 0.004
    bump.inputs["Distance"].default_value = 0.00008
    set_principled(marble, roughness=0.31, ior=1.47, coat=0.045, subsurface=0.028)

    old_surface_link = next(link for link in links if link.to_node == output and link.to_socket == output.inputs["Surface"])
    old_surface = old_surface_link.from_socket
    links.remove(old_surface_link)

    separate = nodes.new("ShaderNodeSeparateXYZ")
    separate.name = "VENUS_HeadCoordinate"
    separate.location = (520, 720)
    links.new(texcoord.outputs["Generated"], separate.inputs[0])

    head_mask = nodes.new("ShaderNodeValToRGB")
    head_mask.name = "VENUS_HeadPolishMask"
    head_mask.location = (720, 720)
    head_mask.color_ramp.elements[0].position = 0.79
    head_mask.color_ramp.elements[0].color = (0, 0, 0, 1)
    head_mask.color_ramp.elements[1].position = 0.86
    head_mask.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(separate.outputs["Y"], head_mask.inputs["Fac"])

    face_normal = nodes.new("ShaderNodeNormalMap")
    face_normal.name = "VENUS_FaceFineNormal"
    face_normal.location = (720, 500)
    face_normal.inputs["Strength"].default_value = 0.16
    source_normal_color_link = next(link for link in links if link.to_node == source_normal and link.to_socket == source_normal.inputs["Color"])
    links.new(source_normal_color_link.from_socket, face_normal.inputs["Color"])

    face = nodes.new("ShaderNodeBsdfPrincipled")
    face.name = "VENUS_FacePolishedCarrara"
    face.label = "VENUS_FacePolishedCarrara"
    face.location = (980, 520)
    set_principled(face, roughness=0.265, ior=1.47, coat=0.035, subsurface=0.045)
    marble_color_link = next(link for link in links if link.to_node == marble and link.to_socket == marble.inputs["Base Color"])
    links.new(marble_color_link.from_socket, face.inputs["Base Color"])
    links.new(face_normal.outputs["Normal"], face.inputs["Normal"])

    mix = nodes.new("ShaderNodeMixShader")
    mix.name = "VENUS_MixFacePolish"
    mix.location = (1240, 340)
    links.new(head_mask.outputs["Color"], mix.inputs[0])
    links.new(old_surface, mix.inputs[1])
    links.new(face.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs["Surface"])
    return material


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


def render_face_review() -> None:
    scene = bpy.context.scene
    old_camera = scene.camera
    old_resolution = (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage)
    old_filepath = scene.render.filepath

    remove_collection(REVIEW_COLLECTION)
    collection = bpy.data.collections.new(REVIEW_COLLECTION)
    scene.collection.children.link(collection)
    data = bpy.data.cameras.new("VENUS_Face_Review_Camera")
    camera = bpy.data.objects.new("VENUS_Face_Review_Camera", data)
    collection.objects.link(camera)
    camera.data.lens = 92
    camera.location = (2.15, -2.1, 2.88)
    look_at(camera, Vector((2.15, 0.0, 2.78)))
    scene.camera = camera

    target = Vector((2.15, 0.0, 2.80))
    add_area_light(collection, "VENUS_Face_Key", (0.9, -1.1, 3.42), 430, 1.15, (1.0, 0.84, 0.72), target)
    add_area_light(collection, "VENUS_Face_Fill", (3.25, -0.65, 2.95), 145, 1.1, (0.62, 0.76, 1.0), target)
    add_area_light(collection, "VENUS_Face_Rim", (2.75, 0.75, 3.35), 300, 0.8, (0.52, 0.67, 1.0), target)

    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OUTPUT_DIR / "face-refined.png")
    bpy.ops.render.render(write_still=True)

    scene.camera = old_camera
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = old_resolution
    scene.render.filepath = old_filepath
    remove_collection(REVIEW_COLLECTION)


def main() -> None:
    statue = bpy.data.objects.get(STATUE_NAME)
    if statue is None or statue.type != "MESH":
        raise RuntimeError(f"Missing mesh: {STATUE_NAME}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    material = refine_face_material(statue)
    render_face_review()
    statue["VENUS_FACE_REFINEMENT"] = "procedural_head_mask_low_normal"
    bpy.context.scene["VENUS_STAGE"] = "face_refined"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print({"blend": str(BLEND_PATH), "material": material.name, "preview": str(OUTPUT_DIR / "face-refined.png")})


try:
    main()
except Exception:
    traceback.print_exc()
    raise
