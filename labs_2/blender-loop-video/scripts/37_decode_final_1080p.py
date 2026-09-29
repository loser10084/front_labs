"""Decode five H.264 checkpoints using Blender's video sequencer."""

import json
import time
import traceback
from pathlib import Path

import bpy


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
VIDEO = PROJECT / "output" / "venus-restoration-v17-final-1080p.mp4"
OUTPUT_DIR = PROJECT / "renders" / "previews" / "final-encoded-check-1080p"
FRAMES = (1, 76, 151, 226, 300)


def main():
    if not VIDEO.is_file():
        raise RuntimeError(f"Missing final video: {VIDEO}")
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 300
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    strip = scene.sequence_editor_create().sequences.new_movie(
        "Encoded Venus final", str(VIDEO), channel=1, frame_start=1
    )
    if strip.frame_final_end != 301:
        raise RuntimeError(f"Final MP4 is not 300 frames: {strip.frame_final_end}")
    scene.render.use_sequencer = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {"video": str(VIDEO), "frames": []}
    for frame in FRAMES:
        scene.frame_set(frame)
        output = OUTPUT_DIR / f"decoded-{frame:03d}.png"
        if output.exists():
            raise RuntimeError(f"Decoded checkpoint already exists: {output}")
        scene.render.filepath = str(output)
        started = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        if not output.is_file() or output.stat().st_size < 1000:
            raise RuntimeError(f"Failed to decode frame {frame}: {output}")
        report["frames"].append({"frame": frame, "bytes": output.stat().st_size, "seconds": round(time.perf_counter() - started, 3)})
    (OUTPUT_DIR / "decode-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False), flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    raise
