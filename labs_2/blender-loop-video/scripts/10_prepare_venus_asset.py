"""Prepare the imported Hunyuan Venus for non-destructive inspection renders."""

from pathlib import Path
import math
import traceback

import bpy
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BLEND_PATH = PROJECT / "blend" / "venus-restoration-v03-working.blend"
PREVIEW_DIR = PROJECT / "renders" / "previews" / "venus-inspection"
TARGET_HEIGHT_M = 3.4


def remove_collection(name: str) -> None:
    collection = bpy.data.collections.get(name)
    if collection is None:
        return
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def find_source_mesh() -> bpy.types.Object:
    candidates = [
        obj
        for obj in bpy.data.objects
        if obj.type == "MESH" and obj.get("VENUS_SOURCE") == "hunyuan-v1"
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one tagged Hunyuan mesh, found {len(candidates)}")
    return candidates[0]


def ensure_collection(name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for old_collection in list(obj.users_collection):
        old_collection.objects.unlink(obj)
    collection.objects.link(obj)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_material(name: str, color: tuple[float, float, float, float], roughness: float):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    principled = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Roughness"].default_value = roughness
    return material


def add_area_light(collection, name, location, energy, size, color, target):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)
    return obj


def main() -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))

    statue = find_source_mesh()
    statue.name = "VENUS_Hunyuan_Working"
    statue.data.name = "VENUS_Hunyuan_Working_Mesh"
    asset_collection = ensure_collection("VENUS_ASSET")
    move_to_collection(statue, asset_collection)

    for collection in bpy.data.collections:
        if collection.name.startswith("LOOP10_"):
            collection.hide_viewport = True
            collection.hide_render = True

    initial_world_corners = [statue.matrix_world @ Vector(corner) for corner in statue.bound_box]
    current_height = max(v.z for v in initial_world_corners) - min(v.z for v in initial_world_corners)
    if current_height <= 0:
        raise RuntimeError("Imported statue has zero height")
    uniform_scale = TARGET_HEIGHT_M / current_height
    statue.scale = tuple(component * uniform_scale for component in statue.scale)
    bpy.context.view_layer.objects.active = statue
    statue.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    statue.select_set(False)

    world_corners = [statue.matrix_world @ Vector(corner) for corner in statue.bound_box]
    min_corner = Vector((min(v.x for v in world_corners), min(v.y for v in world_corners), min(v.z for v in world_corners)))
    max_corner = Vector((max(v.x for v in world_corners), max(v.y for v in world_corners), max(v.z for v in world_corners)))
    statue.location.x -= (min_corner.x + max_corner.x) * 0.5
    statue.location.y -= (min_corner.y + max_corner.y) * 0.5
    statue.location.z -= min_corner.z
    statue["VENUS_TARGET_HEIGHT_M"] = TARGET_HEIGHT_M
    statue["VENUS_STAGE"] = "normalized_raw_material"

    remove_collection("VENUS_INSPECTION")
    inspection = ensure_collection("VENUS_INSPECTION")

    bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, -0.015))
    floor = bpy.context.view_layer.objects.active
    if floor is None:
        raise RuntimeError("Inspection floor was created but no active object was returned")
    floor.name = "VENUS_Inspection_Floor"
    move_to_collection(floor, inspection)
    floor.data.materials.append(make_material("VENUS_Inspection_Floor_Mat", (0.025, 0.028, 0.032, 1), 0.31))

    target = Vector((0, 0, 1.72))
    add_area_light(inspection, "VENUS_Key", (-3.5, -4.0, 5.4), 1250, 3.0, (1.0, 0.78, 0.62), target)
    add_area_light(inspection, "VENUS_Fill", (3.2, -2.2, 3.3), 700, 2.5, (0.48, 0.68, 1.0), target)
    add_area_light(inspection, "VENUS_Rim", (1.0, 3.4, 4.8), 1050, 2.2, (0.55, 0.72, 1.0), target)

    camera_data = bpy.data.cameras.new("VENUS_Inspection_Camera")
    camera_data.lens = 72
    camera = bpy.data.objects.new("VENUS_Inspection_Camera", camera_data)
    inspection.objects.link(camera)
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.world.color = (0.012, 0.014, 0.018)

    views = {
        "front": Vector((0, -6.7, 1.74)),
        "right": Vector((6.7, 0, 1.74)),
        "back": Vector((0, 6.7, 1.74)),
        "left": Vector((-6.7, 0, 1.74)),
    }
    for label, location in views.items():
        camera.location = location
        look_at(camera, target)
        scene.render.filepath = str(PREVIEW_DIR / f"raw-{label}.png")
        bpy.ops.render.render(write_still=True)

    scene["VENUS_STAGE"] = "inspection_rendered"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    final_world_corners = [statue.matrix_world @ Vector(corner) for corner in statue.bound_box]
    final_dimensions = [
        max(v[i] for v in final_world_corners) - min(v[i] for v in final_world_corners)
        for i in range(3)
    ]
    print(
        {
            "blend": str(BLEND_PATH),
            "statue": statue.name,
            "world_dimensions_m": [round(value, 4) for value in final_dimensions],
            "preview_dir": str(PREVIEW_DIR),
            "views": list(views),
        }
    )


try:
    main()
except Exception:
    traceback.print_exc()
    raise
