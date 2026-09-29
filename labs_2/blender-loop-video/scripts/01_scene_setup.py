import bpy
import json
import os


PROJECT_ROOT = r"D:\project\AI\frontend_labs\labs_2\blender-loop-video"
BLEND_PATH = os.path.join(PROJECT_ROOT, "blend", "liquid-monument-v01.blend")
FRAME_OUTPUT = os.path.join(PROJECT_ROOT, "renders", "frames") + os.sep


def enum_identifiers(owner, property_name):
    return {
        item.identifier
        for item in owner.bl_rna.properties[property_name].enum_items
    }


def require_enum(owner, property_name, value):
    available = enum_identifiers(owner, property_name)
    if value not in available:
        raise RuntimeError(
            f"Unsupported enum {property_name}={value!r}; available={sorted(available)}"
        )
    setattr(owner, property_name, value)


os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
os.makedirs(FRAME_OUTPUT, exist_ok=True)

if os.path.exists(BLEND_PATH):
    current_path = os.path.normcase(os.path.abspath(bpy.data.filepath or ""))
    target_path = os.path.normcase(os.path.abspath(BLEND_PATH))
    if current_path != target_path:
        raise FileExistsError(f"Refusing to overwrite existing experiment file: {BLEND_PATH}")

scene = bpy.context.scene
scene.name = "LOOP10_LiquidMonument"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.fps = 30
scene.render.fps_base = 1.0
scene.frame_start = 1
scene.frame_end = 300
scene.frame_set(1)
scene.render.filepath = FRAME_OUTPUT
scene.render.film_transparent = False

require_enum(scene.render.image_settings, "file_format", "PNG")
require_enum(scene.render.image_settings, "color_mode", "RGB")
require_enum(scene.render.image_settings, "color_depth", "8")
scene.render.image_settings.compression = 15

view_transform_values = enum_identifiers(scene.view_settings, "view_transform")
if "AgX" in view_transform_values:
    scene.view_settings.view_transform = "AgX"

scene["loop10_project"] = "Liquid Monument"
scene["loop10_duration_seconds"] = 10.0
scene["loop10_period_frames"] = 300
scene["loop10_validation_frame"] = 301
scene["loop10_preview_resolution"] = "1280x720"
scene["loop10_final_resolution"] = "1920x1080"

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH, check_existing=False)

print(
    json.dumps(
        {
            "stage": "gate-0-scene-setup",
            "blend_path": bpy.data.filepath,
            "scene": scene.name,
            "engine": scene.render.engine,
            "resolution": [
                scene.render.resolution_x,
                scene.render.resolution_y,
                scene.render.resolution_percentage,
            ],
            "fps": scene.render.fps / scene.render.fps_base,
            "frame_range": [scene.frame_start, scene.frame_end],
            "validation_frame": scene["loop10_validation_frame"],
            "image_format": scene.render.image_settings.file_format,
            "color_mode": scene.render.image_settings.color_mode,
            "color_depth": scene.render.image_settings.color_depth,
            "view_transform": scene.view_settings.view_transform,
            "output": scene.render.filepath,
            "objects_preserved": sorted(obj.name for obj in scene.objects),
        },
        ensure_ascii=False,
    )
)
