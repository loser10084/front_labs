"""Encode verified 1080p PNGs as the final high-quality H.264 loop."""

import json
import struct
import time
import traceback
from pathlib import Path

import bpy


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
FRAMES_DIR = PROJECT / "renders" / "frames" / "venus-final-1080p"
OUTPUT = PROJECT / "output" / "venus-restoration-v17-final-1080p.mp4"
EDIT_BLEND = PROJECT / "blend" / "venus-restoration-v17-final-encode.blend"
REPORT = PROJECT / "output" / "venus-restoration-v17-final-encode-report.json"
FRAMES = [FRAMES_DIR / f"venus-final-{frame:03d}.png" for frame in range(1, 301)]


def dimensions(path):
    with path.open("rb") as stream:
        header = stream.read(24)
        if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            raise RuntimeError(f"Not a PNG: {path}")
        return struct.unpack(">II", header[16:24])


def main():
    missing = [path.name for path in FRAMES if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} frames; first: {missing[:8]}")
    invalid = [path.name for path in FRAMES if dimensions(path) != (1920, 1080)]
    if invalid:
        raise RuntimeError(f"Wrong PNG dimensions: {invalid[:8]}")
    if OUTPUT.exists() or EDIT_BLEND.exists():
        raise RuntimeError(f"Final output or edit project already exists: {OUTPUT}, {EDIT_BLEND}")

    scene = bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 300
    # Input PNGs already carry the scene's AgX display colors.
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    editor = scene.sequence_editor_create()
    strip = editor.sequences.new_image("Venus 1080p final", str(FRAMES[0]), channel=1, frame_start=1)
    for path in FRAMES[1:]:
        strip.elements.append(path.name)
    if strip.frame_final_end != 301:
        raise RuntimeError(f"Unexpected image-strip end: {strip.frame_final_end}")

    scene.render.use_sequencer = True
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.audio_codec = "NONE"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.gopsize = 30
    scene.render.filepath = str(OUTPUT)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(EDIT_BLEND))

    started = time.perf_counter()
    print(json.dumps({"stage": "encode_start", "frames": 300, "output": str(OUTPUT)}), flush=True)
    bpy.ops.render.render(animation=True)
    seconds = round(time.perf_counter() - started, 3)
    if not OUTPUT.is_file() or OUTPUT.stat().st_size == 0:
        raise RuntimeError(f"Blender did not write the MP4: {OUTPUT}")
    report = {
        "source_frames": str(FRAMES_DIR),
        "frame_count": 300,
        "resolution": [1920, 1080],
        "fps": 30,
        "codec": "H264",
        "quality": "HIGH",
        "output": str(OUTPUT),
        "bytes": OUTPUT.stat().st_size,
        "encode_seconds": seconds,
        "edit_blend": str(EDIT_BLEND),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"stage": "encode_complete", **report}), flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    raise
