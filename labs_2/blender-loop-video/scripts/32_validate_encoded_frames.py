"""Decode representative frames from the 720p MP4 through Blender's VSE."""

import json
import time
import traceback
from pathlib import Path

import bpy


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
VIDEO = PROJECT / "output" / "venus-restoration-v17-preview-720p.mp4"
OUTPUT_DIR = PROJECT / "renders" / "previews" / "cinematic-loop-720p" / "encoded-check"
FRAMES = (1, 76, 151, 226, 300)


def main():
    if not VIDEO.is_file():
        raise RuntimeError(f"Video is missing: {VIDEO}")
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 300
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    strip = scene.sequence_editor_create().sequences.new_movie(
        "Encoded Venus preview", str(VIDEO), channel=1, frame_start=1
    )
    if strip.frame_final_end != 301:
        raise RuntimeError(f"Decoded movie length is not 300 frames: {strip.frame_final_end}")
    scene.render.use_sequencer = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {"video": str(VIDEO), "frames": []}
    for frame in FRAMES:
        scene.frame_set(frame)
        output = OUTPUT_DIR / f"encoded-{frame:03d}.png"
        scene.render.filepath = str(output)
        started = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        if not output.is_file() or output.stat().st_size < 1000:
            raise RuntimeError(f"Failed to decode frame {frame}: {output}")
        report["frames"].append({
            "frame": frame,
            "output": str(output),
            "bytes": output.stat().st_size,
            "seconds": round(time.perf_counter() - started, 3),
        })
    report_path = OUTPUT_DIR / "decode-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False), flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    raise
