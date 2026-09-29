"""Add a removable museum plinth and render final model-review frames."""

from pathlib import Path
import traceback

import bpy
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BLEND_PATH = PROJECT / "blend" / "venus-restoration-v07-review.blend"
PREVIEW_DIR = PROJECT / "renders" / "previews" / "venus-final-review"


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def remove_collection(name: str) -> None:
    collection = bpy.data.collections.get(name)
    if collection is None:
        return
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for old_collection in list(obj.users_collection):
        old_collection.objects.unlink(obj)
    collection.objects.link(obj)


def principled_material(name, color, metallic, roughness):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    principled = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Metallic"].default_value = metallic
    principled.inputs["Roughness"].default_value = roughness
    return material


def build_plinth() -> bpy.types.Object:
    remove_collection("VENUS_PRESENTATION")
    collection = bpy.data.collections.new("VENUS_PRESENTATION")
    bpy.context.scene.collection.children.link(collection)

    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.78, depth=0.14, location=(0, 0, 0.07))
    plinth = bpy.context.view_layer.objects.active
    if plinth is None:
        raise RuntimeError("Failed to create museum plinth")
    plinth.name = "VENUS_Museum_Plinth"
    plinth.scale.y = 0.84
    bpy.context.view_layer.objects.active = plinth
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to_collection(plinth, collection)
    plinth.data.materials.append(principled_material("VENUS_Black_Basalt", (0.012, 0.014, 0.018, 1), 0.08, 0.24))
    bevel = plinth.modifiers.new("VENUS_Plinth_Edge", "BEVEL")
    bevel.width = 0.022
    bevel.segments = 4

    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.705,
        minor_radius=0.006,
        major_segments=96,
        minor_segments=12,
        location=(0, 0, 0.145),
    )
    inlay = bpy.context.view_layer.objects.active
    if inlay is None:
        raise RuntimeError("Failed to create plinth inlay")
    inlay.name = "VENUS_Plinth_Inlay"
    inlay.scale.y = 0.84
    bpy.context.view_layer.objects.active = inlay
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to_collection(inlay, collection)
    inlay.data.materials.append(principled_material("VENUS_Aged_Bronze", (0.12, 0.055, 0.018, 1), 0.92, 0.31))

    collection["VENUS_OPTIONAL"] = True
    return plinth


def render_review() -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    camera = bpy.data.objects.get("VENUS_Inspection_Camera")
    if camera is None:
        raise RuntimeError("Inspection camera is missing")
    scene.camera = camera
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100

    camera.data.lens = 78
    camera.location = (3.7, -6.5, 2.15)
    look_at(camera, Vector((0, 0, 1.72)))
    scene.render.filepath = str(PREVIEW_DIR / "venus-review-full.png")
    bpy.ops.render.render(write_still=True)

    camera.data.lens = 92
    camera.location = (2.35, -4.15, 2.72)
    look_at(camera, Vector((0, 0, 2.35)))
    scene.render.filepath = str(PREVIEW_DIR / "venus-review-detail.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    statue = bpy.data.objects.get("VENUS_Hunyuan_Working")
    if statue is None:
        raise RuntimeError("Refined Venus mesh is missing")
    build_plinth()
    render_review()
    statue["VENUS_STAGE"] = "review_candidate"
    bpy.context.scene["VENUS_STAGE"] = "review_candidate"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print({"blend": str(BLEND_PATH), "review_dir": str(PREVIEW_DIR), "optional_plinth": True})


try:
    main()
except Exception:
    traceback.print_exc()
    raise
