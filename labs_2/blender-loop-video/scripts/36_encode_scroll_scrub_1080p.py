"""Encode the final PNG sequence as an all-intra H.264 file for scroll scrubbing."""

import json
import struct
import time
import traceback
from pathlib import Path

import bpy


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
FRAMES_DIR = PROJECT / "renders" / "frames" / "venus-final-1080p"
OUTPUT = PROJECT / "output" / "venus-restoration-v17-scroll-scrub-1080p.mp4"
REPORT = PROJECT / "output" / "venus-restoration-v17-scroll-scrub-encode-report.json"
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
    if OUTPUT.exists() or REPORT.exists():
        raise RuntimeError(f"Scroll-scrub output already exists: {OUTPUT}, {REPORT}")

    scene = bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 300
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    editor = scene.sequence_editor_create()
    strip = editor.sequences.new_image(
        "Venus 1080p scroll scrub",
        str(FRAMES[0]),
        channel=1,
        frame_start=1,
    )
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
    # Every frame is independently decodable. This intentionally favors seek
    # latency over file size because this asset is for local scroll testing.
    scene.render.ffmpeg.gopsize = 1
    scene.render.filepath = str(OUTPUT)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    print(
        json.dumps(
            {
                "stage": "scroll_scrub_encode_start",
                "frames": 300,
                "gop_size": 1,
                "output": str(OUTPUT),
            }
        ),
        flush=True,
    )
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
        "gop_size": 1,
        "purpose": "local scroll scrubbing",
        "output": str(OUTPUT),
        "bytes": OUTPUT.stat().st_size,
        "encode_seconds": seconds,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"stage": "scroll_scrub_encode_complete", **report}), flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    raise
