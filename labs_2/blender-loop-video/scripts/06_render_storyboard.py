import bpy
import json
import os
import time


PROJECT_ROOT = r"D:\project\AI\frontend_labs\labs_2\blender-loop-video"
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "renders", "previews", "gate-1")
FINAL_OUTPUT = os.path.join(PROJECT_ROOT, "renders", "frames") + os.sep
STORYBOARD_FRAMES = (1, 76, 151, 226)


os.makedirs(OUTPUT_DIR, exist_ok=True)

scene = bpy.context.scene
if scene.name != "LOOP10_LiquidMonument":
    raise RuntimeError(f"Unexpected scene: {scene.name!r}")
if not scene.camera or scene.camera.name != "LOOP10_Camera":
    raise RuntimeError("Gate 1 camera is missing")

scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"
scene.render.image_settings.compression = 25

rendered = []
started = time.perf_counter()

for frame in STORYBOARD_FRAMES:
    scene.frame_set(frame)
    path = os.path.join(OUTPUT_DIR, f"liquid-monument-graybox-{frame:03d}.png")
    scene.render.filepath = path
    frame_started = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    rendered.append(
        {
            "frame": frame,
            "path": path,
            "seconds": round(time.perf_counter() - frame_started, 3),
            "bytes": os.path.getsize(path),
        }
    )

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.filepath = FINAL_OUTPUT
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, check_existing=False)

print(
    json.dumps(
        {
            "stage": "gate-1-storyboard",
            "total_seconds": round(time.perf_counter() - started, 3),
            "rendered": rendered,
            "restored_resolution": [
                scene.render.resolution_x,
                scene.render.resolution_y,
            ],
            "restored_output": scene.render.filepath,
        },
        ensure_ascii=False,
    )
)
