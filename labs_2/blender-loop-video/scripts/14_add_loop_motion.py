"""Add restrained periodic atmosphere and validate the 300-frame loop."""

from pathlib import Path
import math
import random
import traceback

import bpy
from mathutils import Vector


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BLEND_PATH = PROJECT / "blend" / "venus-restoration-v09-motion-gate.blend"
PREVIEW_DIR = PROJECT / "renders" / "previews" / "motion-gate"


def remove_collection(name: str) -> None:
    collection = bpy.data.collections.get(name)
    if collection is None:
        return
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_driver(owner, data_path, index, expression):
    curve = owner.driver_add(data_path, index)
    curve.driver.type = "SCRIPTED"
    curve.driver.expression = expression


def make_emission_material(name, color, strength):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = strength
    links.new(emission.outputs[0], output.inputs["Surface"])
    return material


def add_arch(collection):
    existing = bpy.data.objects.get("VENUS_Ritual_Arch")
    if existing is not None:
        bpy.data.objects.remove(existing, do_unlink=True)
    curve_data = bpy.data.curves.new("VENUS_Ritual_Arch_Curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.bevel_depth = 0.055
    curve_data.bevel_resolution = 4
    spline = curve_data.splines.new("POLY")
    segments = 40
    spline.points.add(segments)
    center_x = 2.45
    center_z = 3.72
    radius_x = 2.0
    radius_z = 2.0
    for index in range(segments + 1):
        angle = math.pi * index / segments
        x = center_x - radius_x * math.cos(angle)
        z = center_z + radius_z * math.sin(angle)
        spline.points[index].co = (x, 4.42, z, 1.0)
    arch = bpy.data.objects.new("VENUS_Ritual_Arch", curve_data)
    collection.objects.link(arch)
    arch.data.materials.append(bpy.data.materials["VENUS_Aged_Bronze"])
    return arch


def add_volume(collection):
    bpy.ops.mesh.primitive_cube_add(location=(0, 1.2, 3.25), scale=(8.3, 6.2, 3.15))
    volume = bpy.context.view_layer.objects.active
    if volume is None:
        raise RuntimeError("Failed to create atmosphere volume")
    volume.name = "VENUS_Atmosphere_Volume"
    for source in list(volume.users_collection):
        source.objects.unlink(volume)
    collection.objects.link(volume)
    material = bpy.data.materials.get("VENUS_Atmosphere") or bpy.data.materials.new("VENUS_Atmosphere")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    volume_node = nodes.new("ShaderNodeVolumePrincipled")
    volume_node.inputs["Density"].default_value = 0.0016
    volume_node.inputs["Anisotropy"].default_value = 0.32
    volume_node.inputs["Color"].default_value = (0.16, 0.2, 0.28, 1)
    links.new(volume_node.outputs["Volume"], output.inputs["Volume"])
    volume.data.materials.append(material)


def add_dust(collection):
    rng = random.Random(220926)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.0045, location=(0, 0, 0))
    template = bpy.context.view_layer.objects.active
    if template is None:
        raise RuntimeError("Failed to create dust template")
    template.name = "VENUS_Dust_00"
    for source in list(template.users_collection):
        source.objects.unlink(template)
    collection.objects.link(template)
    template.data.materials.append(make_emission_material("VENUS_Dust_Material", (0.18, 0.26, 0.38, 1), 0.35))

    particles = [template]
    for index in range(1, 18):
        obj = template.copy()
        obj.data = template.data
        obj.name = f"VENUS_Dust_{index:02d}"
        collection.objects.link(obj)
        particles.append(obj)

    for index, obj in enumerate(particles):
        base_x = rng.uniform(-4.8, 5.2)
        base_y = rng.uniform(-0.8, 4.2)
        base_z = rng.uniform(0.45, 5.8)
        radius = rng.uniform(0.45, 1.15)
        phase = rng.uniform(0, math.tau)
        scale = rng.uniform(0.35, 1.25)
        obj.scale = (scale, scale, scale)
        obj.location = (base_x, base_y, base_z)
        add_driver(obj, "location", 0, f"{base_x:.6f} + {0.08 * radius:.6f}*cos(2*pi*(frame-1)/300 + {phase:.6f})")
        add_driver(obj, "location", 2, f"{base_z:.6f} + {0.18 * radius:.6f}*sin(2*pi*(frame-1)/300 + {phase:.6f})")


def add_scan_light(collection):
    data = bpy.data.lights.new("VENUS_Scan_Light", type="AREA")
    data.shape = "RECTANGLE"
    data.energy = 250
    data.color = (0.32, 0.55, 0.92)
    data.size = 3.2
    data.size_y = 0.14
    obj = bpy.data.objects.new("VENUS_Scan_Light", data)
    collection.objects.link(obj)
    obj.location = (2.5, -0.6, 2.2)
    look_at(obj, (2.15, 0.15, 1.9))
    add_driver(obj, "location", 2, "2.2 + 1.55*sin(2*pi*(frame-1)/300)")
    add_driver(data, "energy", -1, "250 + 35*cos(2*pi*(frame-1)/300)")


def render_frames():
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    for frame in (1, 76, 151, 226, 301):
        scene.frame_set(frame)
        scene.render.filepath = str(PREVIEW_DIR / f"motion-gate-{frame:03d}.png")
        bpy.ops.render.render(write_still=True)
    scene.frame_set(1)


def main():
    hall = bpy.data.collections.get("VENUS_HALL")
    if hall is None:
        raise RuntimeError("Museum hall is missing")
    remove_collection("VENUS_MOTION")
    motion = bpy.data.collections.new("VENUS_MOTION")
    bpy.context.scene.collection.children.link(motion)
    add_arch(hall)
    add_volume(motion)
    add_dust(motion)
    add_scan_light(motion)
    render_frames()
    bpy.context.scene["VENUS_STAGE"] = "motion_gate_rendered"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print({"blend": str(BLEND_PATH), "preview_dir": str(PREVIEW_DIR), "dust_count": 18, "validation_frame": 301})


try:
    main()
except Exception:
    traceback.print_exc()
    raise
