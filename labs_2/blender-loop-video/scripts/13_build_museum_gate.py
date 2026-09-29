"""Build the museum-installation graybox around the refined Venus."""

from pathlib import Path
import math
import traceback

import bpy
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BLEND_PATH = PROJECT / "blend" / "venus-restoration-v08-museum-gate.blend"
PREVIEW_DIR = PROJECT / "renders" / "previews" / "museum-gate"


def remove_collection(name: str) -> None:
    collection = bpy.data.collections.get(name)
    if collection is None:
        return
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def ensure_material(name, color, metallic=0.0, roughness=0.5, emission=None, emission_strength=0.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    principled = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Metallic"].default_value = metallic
    principled.inputs["Roughness"].default_value = roughness
    if emission is not None:
        principled.inputs["Emission Color"].default_value = emission
        principled.inputs["Emission Strength"].default_value = emission_strength
    return material


def move_to_collection(obj, collection) -> None:
    for source in list(obj.users_collection):
        source.objects.unlink(obj)
    collection.objects.link(obj)


def add_box(collection, name, location, scale, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.view_layer.objects.active
    if obj is None:
        raise RuntimeError(f"Failed to create {name}")
    obj.name = name
    obj.scale = scale
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to_collection(obj, collection)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new(f"{name}_Bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    return obj


def add_area_light(collection, name, location, energy, size, color, target):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def add_driver(obj, data_path, index, expression):
    curve = obj.driver_add(data_path, index)
    curve.driver.type = "SCRIPTED"
    curve.driver.expression = expression


def reset_installation_objects() -> list[bpy.types.Object]:
    names = ["VENUS_Hunyuan_Working", "VENUS_Museum_Plinth", "VENUS_Plinth_Inlay"]
    objects = []
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Required installation object is missing: {name}")
        matrix_world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = matrix_world
        obj.location.x = 0.0
        obj.location.y = 0.0
        objects.append(obj)
    return objects


def main() -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    installation_objects = reset_installation_objects()
    remove_collection("VENUS_HALL")
    hall = bpy.data.collections.new("VENUS_HALL")
    bpy.context.scene.collection.children.link(hall)

    for collection_name in ("VENUS_INSPECTION",):
        collection = bpy.data.collections.get(collection_name)
        if collection:
            collection.hide_viewport = True
            collection.hide_render = True

    for name in ("Cube", "Camera", "Light"):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_viewport = True
            obj.hide_render = True

    root = bpy.data.objects.new("VENUS_Installation_Root", None)
    hall.objects.link(root)
    for obj in installation_objects:
        world = obj.matrix_world.copy()
        obj.parent = root
        obj.matrix_world = world
    root.location = (2.15, 0.0, 0.0)

    floor_mat = ensure_material("VENUS_Hall_Floor", (0.016, 0.019, 0.024, 1), metallic=0.32, roughness=0.18)
    wall_mat = ensure_material("VENUS_Hall_Wall", (0.028, 0.032, 0.039, 1), metallic=0.06, roughness=0.4)
    frame_mat = ensure_material("VENUS_Hall_Frame", (0.012, 0.014, 0.018, 1), metallic=0.58, roughness=0.23)
    slit_mat = ensure_material(
        "VENUS_Hall_LightSlit",
        (0.12, 0.18, 0.22, 1),
        roughness=0.25,
        emission=(0.24, 0.48, 0.62, 1),
        emission_strength=2.1,
    )

    add_box(hall, "VENUS_Hall_Floor", (0, 1.2, -0.13), (9.0, 9.0, 0.12), floor_mat, 0.04)
    add_box(hall, "VENUS_Hall_BackWall", (0, 5.2, 3.6), (9.0, 0.28, 3.7), wall_mat, 0.08)
    add_box(hall, "VENUS_Hall_LeftWall", (-7.0, 0.7, 3.4), (0.24, 4.8, 3.5), wall_mat, 0.06)
    add_box(hall, "VENUS_Hall_Ceiling", (0, 1.2, 7.0), (9.0, 5.2, 0.18), wall_mat, 0.06)

    add_box(hall, "VENUS_Portal_Left", (0.15, 4.55, 3.05), (0.32, 0.52, 3.05), frame_mat, 0.08)
    add_box(hall, "VENUS_Portal_Right", (4.75, 4.55, 3.05), (0.32, 0.52, 3.05), frame_mat, 0.08)
    add_box(hall, "VENUS_Portal_Top", (2.45, 4.55, 6.0), (2.62, 0.52, 0.28), frame_mat, 0.08)

    add_box(hall, "VENUS_Left_LightSlit_A", (-5.5, 4.88, 3.25), (0.035, 0.04, 2.25), slit_mat)
    add_box(hall, "VENUS_Left_LightSlit_B", (-3.65, 4.88, 4.0), (0.025, 0.04, 1.35), slit_mat)
    add_box(hall, "VENUS_Right_LightSlit", (5.65, 4.88, 4.15), (0.03, 0.04, 1.45), slit_mat)

    add_box(hall, "VENUS_Foreground_Pier", (-6.0, -2.0, 2.7), (0.6, 0.62, 2.8), frame_mat, 0.12)
    add_box(hall, "VENUS_Back_Step", (2.35, 3.2, 0.16), (3.0, 1.2, 0.16), wall_mat, 0.06)

    add_area_light(hall, "VENUS_Hall_Key", (4.8, -3.8, 5.8), 1450, 3.0, (1.0, 0.72, 0.5), (2.15, 0, 1.9))
    add_area_light(hall, "VENUS_Hall_Fill", (-2.8, -2.3, 3.8), 820, 3.8, (0.38, 0.58, 1.0), (1.4, 0, 1.8))
    add_area_light(hall, "VENUS_Hall_Rim", (3.8, 3.5, 5.2), 1180, 2.4, (0.42, 0.68, 1.0), (2.15, 0, 2.0))
    add_area_light(hall, "VENUS_Hall_LeftWash", (-4.5, 2.5, 4.8), 500, 4.5, (0.24, 0.34, 0.55), (-3.8, 4.8, 3.2))

    target = bpy.data.objects.new("VENUS_Camera_Target", None)
    hall.objects.link(target)
    target.location = (0.62, 0.0, 1.82)
    add_driver(target, "location", 0, "0.62 + 0.05*cos(2*pi*(frame-1)/300)")

    camera_data = bpy.data.cameras.new("VENUS_Hall_Camera")
    camera_data.lens = 58
    camera_data.dof.use_dof = True
    camera_data.dof.focus_object = target
    camera_data.dof.aperture_fstop = 3.8
    camera = bpy.data.objects.new("VENUS_Hall_Camera", camera_data)
    hall.objects.link(camera)
    camera.location = (0.0, -8.65, 2.55)
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.name = "VENUS_CameraTrack"
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    add_driver(camera, "location", 0, "0.22*sin(2*pi*(frame-1)/300)")
    add_driver(camera, "location", 1, "-8.65 + 0.16*cos(2*pi*(frame-1)/300)")
    add_driver(camera, "location", 2, "2.55 + 0.07*sin(2*pi*(frame-1)/300)")

    scene = bpy.context.scene
    scene.name = "VENUS_Museum_Loop"
    scene.camera = camera
    scene.frame_start = 1
    scene.frame_end = 300
    scene["LOOP_VALIDATION_FRAME"] = 301
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.world.color = (0.004, 0.005, 0.008)

    for frame in (1, 76, 151, 226):
        scene.frame_set(frame)
        scene.render.filepath = str(PREVIEW_DIR / f"museum-gate-{frame:03d}.png")
        bpy.ops.render.render(write_still=True)

    scene.frame_set(1)
    scene["VENUS_STAGE"] = "museum_gate_rendered"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print(
        {
            "blend": str(BLEND_PATH),
            "preview_dir": str(PREVIEW_DIR),
            "frames": [1, 76, 151, 226],
            "camera": camera.name,
            "statue_root_x": root.location.x,
        }
    )


try:
    main()
except Exception:
    traceback.print_exc()
    raise
