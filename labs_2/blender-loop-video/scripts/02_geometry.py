import bpy
import json
import math
from mathutils import Vector


PREFIX = "LOOP10_"
SCENE_NAME = "LOOP10_LiquidMonument"


def remove_experiment_data():
    for obj in list(bpy.data.objects):
        if obj.name.startswith(PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)

    for collection in list(bpy.data.collections):
        if collection.name.startswith(PREFIX):
            bpy.data.collections.remove(collection)

    for material in list(bpy.data.materials):
        if material.name.startswith(PREFIX):
            bpy.data.materials.remove(material)

    for mesh in list(bpy.data.meshes):
        if mesh.name.startswith(PREFIX):
            bpy.data.meshes.remove(mesh)

    for curve in list(bpy.data.curves):
        if curve.name.startswith(PREFIX):
            bpy.data.curves.remove(curve)


def create_collection(name, parent):
    collection = bpy.data.collections.new(name)
    parent.children.link(collection)
    return collection


def material_input(node, identifier):
    return next(socket for socket in node.inputs if socket.identifier == identifier)


def make_material(name, color, roughness, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    principled = next(
        node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"
    )
    material_input(principled, "Base Color").default_value = (*color, 1.0)
    material_input(principled, "Metallic").default_value = metallic
    material_input(principled, "Roughness").default_value = roughness
    return material


def link_object(obj, collection):
    collection.objects.link(obj)
    return obj


def make_box(name, location, dimensions, collection, material, bevel=0.12):
    vertices = [
        (-0.5, -0.5, -0.5),
        (0.5, -0.5, -0.5),
        (0.5, 0.5, -0.5),
        (-0.5, 0.5, -0.5),
        (-0.5, -0.5, 0.5),
        (0.5, -0.5, 0.5),
        (0.5, 0.5, 0.5),
        (-0.5, 0.5, 0.5),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (4, 0, 3, 7),
    ]
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = link_object(bpy.data.objects.new(name, mesh), collection)
    obj.location = location
    obj.dimensions = dimensions
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)
    obj.data.materials.append(material)
    if bevel > 0:
        modifier = obj.modifiers.new(f"{name}_Bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    return obj


def make_ribbon(
    name,
    radius,
    width,
    z_base,
    z_wave,
    wave_frequency,
    twist_count,
    phase,
    location,
    rotation,
    collection,
    material,
):
    segments = 192
    width_segments = 6
    vertices = []
    faces = []

    for segment in range(segments):
        u = math.tau * segment / segments
        radial = Vector((math.cos(u), math.sin(u), 0.0))
        center = Vector(
            (
                radius * math.cos(u),
                radius * 0.76 * math.sin(u),
                z_base + z_wave * math.sin(wave_frequency * u + phase),
            )
        )
        twist = twist_count * u + phase
        across = Vector((0.0, 0.0, 1.0)) * math.cos(twist) + radial * math.sin(twist)

        for width_index in range(width_segments):
            factor = width_index / (width_segments - 1) - 0.5
            point = center + across * (factor * width)
            vertices.append(tuple(point))

    for segment in range(segments):
        next_segment = (segment + 1) % segments
        for width_index in range(width_segments - 1):
            a = segment * width_segments + width_index
            b = next_segment * width_segments + width_index
            faces.append((a, b, b + 1, a + 1))

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for polygon in mesh.polygons:
        polygon.use_smooth = True

    obj = link_object(bpy.data.objects.new(name, mesh), collection)
    obj.location = location
    obj.rotation_euler = rotation
    obj.data.materials.append(material)

    solidify = obj.modifiers.new(f"{name}_Solidify", "SOLIDIFY")
    solidify.thickness = 0.12
    solidify.offset = 0.0
    bevel = obj.modifiers.new(f"{name}_Bevel", "BEVEL")
    bevel.width = 0.055
    bevel.segments = 3

    return obj


def make_closed_curve(name, points, bevel_depth, collection, material):
    curve_data = bpy.data.curves.new(name=f"{name}_Curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 2
    curve_data.bevel_depth = bevel_depth
    curve_data.bevel_resolution = 4
    spline = curve_data.splines.new("NURBS")
    spline.points.add(len(points) - 1)
    for point, coordinate in zip(spline.points, points):
        point.co = (*coordinate, 1.0)
    spline.use_cyclic_u = True
    spline.order_u = min(4, len(points))
    spline.use_endpoint_u = False
    obj = link_object(bpy.data.objects.new(name, curve_data), collection)
    obj.data.materials.append(material)
    return obj


def aim_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_area_light(name, location, energy, size, color, target, collection):
    data = bpy.data.lights.new(name=f"{name}_Data", type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = link_object(bpy.data.objects.new(name, data), collection)
    obj.location = location
    aim_at(obj, target)
    return obj


def set_linear_animation(obj, end_rotation_z):
    start_rotation = obj.rotation_euler.copy()
    obj.rotation_euler = start_rotation
    obj.keyframe_insert(data_path="rotation_euler", frame=1)
    obj.rotation_euler.z = end_rotation_z
    obj.keyframe_insert(data_path="rotation_euler", frame=301)
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "LINEAR"


scene = bpy.context.scene
if scene.name != SCENE_NAME:
    raise RuntimeError(f"Expected scene {SCENE_NAME!r}, found {scene.name!r}")
if not bpy.data.filepath.endswith("liquid-monument-v01.blend"):
    raise RuntimeError(f"Unexpected Blender file: {bpy.data.filepath!r}")

remove_experiment_data()

for default_name in ("Cube", "Camera", "Light"):
    default_object = bpy.data.objects.get(default_name)
    if default_object:
        default_object.hide_render = True
        default_object.hide_viewport = True

root = create_collection("LOOP10_ROOT", scene.collection)
sculpture = create_collection("LOOP10_SCULPTURE", root)
foreground = create_collection("LOOP10_FOREGROUND", root)
background = create_collection("LOOP10_BACKGROUND", root)
lights = create_collection("LOOP10_LIGHTS", root)
cameras = create_collection("LOOP10_CAMERAS", root)

mat_sculpture = make_material("LOOP10_MAT_Sculpture", (0.44, 0.48, 0.53), 0.32, 0.34)
mat_secondary = make_material("LOOP10_MAT_Secondary", (0.19, 0.22, 0.27), 0.5, 0.08)
mat_trace = make_material("LOOP10_MAT_Trace", (0.72, 0.78, 0.86), 0.24, 0.12)
mat_floor = make_material("LOOP10_MAT_Floor", (0.035, 0.045, 0.06), 0.26, 0.2)
mat_arch = make_material("LOOP10_MAT_Architecture", (0.08, 0.1, 0.13), 0.48, 0.1)

center = (2.15, 0.0, 3.3)
ribbon_a = make_ribbon(
    "LOOP10_Ribbon_A",
    3.45,
    1.26,
    0.0,
    0.48,
    3,
    2,
    0.15,
    center,
    (math.radians(12), math.radians(-9), math.radians(6)),
    sculpture,
    mat_sculpture,
)
ribbon_b = make_ribbon(
    "LOOP10_Ribbon_B",
    2.55,
    0.82,
    0.0,
    0.36,
    2,
    3,
    1.35,
    center,
    (math.radians(-17), math.radians(22), math.radians(-12)),
    sculpture,
    mat_secondary,
)
ribbon_c = make_ribbon(
    "LOOP10_Ribbon_C",
    1.65,
    0.56,
    0.0,
    0.28,
    4,
    2,
    2.4,
    center,
    (math.radians(28), math.radians(-19), math.radians(14)),
    sculpture,
    mat_sculpture,
)

set_linear_animation(ribbon_a, ribbon_a.rotation_euler.z + math.tau)
set_linear_animation(ribbon_b, ribbon_b.rotation_euler.z - math.tau * 2)
set_linear_animation(ribbon_c, ribbon_c.rotation_euler.z + math.tau * 3)

for trace_index, trace_radius in enumerate((3.0, 2.12, 1.22)):
    points = []
    for index in range(96):
        u = math.tau * index / 96
        points.append(
            (
                center[0] + trace_radius * math.cos(u),
                center[1] + trace_radius * 0.76 * math.sin(u),
                center[2] + 0.2 * math.sin((trace_index + 2) * u + trace_index),
            )
        )
    make_closed_curve(
        f"LOOP10_Trace_{trace_index + 1}",
        points,
        0.035 + trace_index * 0.012,
        sculpture,
        mat_trace,
    )

for index in range(18):
    angle = math.tau * index / 18
    radius = 4.1 + 0.45 * math.sin(index * 1.7)
    location = (
        center[0] + radius * math.cos(angle),
        center[1] + radius * 0.7 * math.sin(angle),
        center[2] + 1.25 * math.sin(angle * 2.0),
    )
    shard = make_box(
        f"LOOP10_Shard_{index + 1:02d}",
        location,
        (0.1 + 0.05 * (index % 3), 0.16, 0.55 + 0.18 * (index % 4)),
        sculpture,
        mat_trace if index % 4 == 0 else mat_secondary,
        bevel=0.04,
    )
    shard.rotation_euler = (angle * 0.3, angle * 0.45, -angle)

floor = make_box(
    "LOOP10_ReflectiveFloor",
    (1.5, 1.8, -0.35),
    (24.0, 22.0, 0.5),
    background,
    mat_floor,
    bevel=0.18,
)

for x in (-4.8, 8.0):
    make_box(
        f"LOOP10_ArchPillar_{'L' if x < 0 else 'R'}",
        (x, 4.6, 4.2),
        (0.55, 1.2, 8.4),
        background,
        mat_arch,
        bevel=0.22,
    )
make_box(
    "LOOP10_ArchBeam",
    (1.6, 4.6, 8.1),
    (13.4, 1.2, 0.55),
    background,
    mat_arch,
    bevel=0.22,
)
make_box(
    "LOOP10_BackWall",
    (2.0, 7.2, 4.2),
    (18.0, 0.4, 9.0),
    background,
    mat_arch,
    bevel=0.1,
)

foreground_panel = make_box(
    "LOOP10_ForegroundFrame",
    (8.65, -2.1, 4.3),
    (0.28, 4.0, 8.6),
    foreground,
    mat_secondary,
    bevel=0.12,
)
foreground_panel.rotation_euler.y = math.radians(-8)

target = (1.3, 0.35, 3.15)
camera_data = bpy.data.cameras.new("LOOP10_Camera_Data")
camera_data.lens = 54.0
camera_data.sensor_width = 36.0
camera_data.dof.use_dof = False
camera = link_object(bpy.data.objects.new("LOOP10_Camera", camera_data), cameras)
camera.location = (10.8, -16.8, 7.6)
aim_at(camera, target)
scene.camera = camera

make_area_light(
    "LOOP10_KeyLight",
    (-3.0, -5.5, 10.5),
    1450.0,
    7.0,
    (0.68, 0.78, 1.0),
    target,
    lights,
)
make_area_light(
    "LOOP10_RimLight",
    (8.5, 3.0, 8.0),
    1800.0,
    5.0,
    (1.0, 0.58, 0.34),
    center,
    lights,
)
make_area_light(
    "LOOP10_FillLight",
    (-4.0, 1.0, 4.2),
    900.0,
    6.0,
    (0.36, 0.5, 0.78),
    center,
    lights,
)

world = bpy.data.worlds.get("LOOP10_World") or bpy.data.worlds.new("LOOP10_World")
world.use_nodes = False
world.color = (0.008, 0.012, 0.02)
scene.world = world

scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, check_existing=False)

print(
    json.dumps(
        {
            "stage": "gate-1-graybox",
            "camera": scene.camera.name,
            "loop10_objects": len([obj for obj in scene.objects if obj.name.startswith(PREFIX)]),
            "ribbons": [ribbon_a.name, ribbon_b.name, ribbon_c.name],
            "collections": sorted(
                collection.name
                for collection in bpy.data.collections
                if collection.name.startswith(PREFIX)
            ),
            "frame": scene.frame_current,
            "saved": bpy.data.filepath,
        },
        ensure_ascii=False,
    )
)

