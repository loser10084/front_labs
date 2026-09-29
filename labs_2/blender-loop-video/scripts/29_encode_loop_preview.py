"""Encode the verified 1–300 PNG sequence into a 10-second H.264 MP4."""

import argparse
import json
import struct
import sys
import time
import traceback
from pathlib import Path

import bpy


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
FRAMES_DIR = PROJECT / "renders" / "previews" / "cinematic-loop-720p" / "frames"
OUTPUT = PROJECT / "output" / "venus-restoration-v17-preview-720p.mp4"
EDIT_BLEND = PROJECT / "blend" / "venus-restoration-v17-preview-encode.blend"
REPORT = PROJECT / "renders" / "previews" / "cinematic-loop-720p" / "encode-report.json"


def image_dimensions(path):
    with path.open("rb") as handle:
        header = handle.read(24)
        if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            raise RuntimeError(f"Not a PNG image: {path}")
        return struct.unpack(">II", header[16:24])


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(argv)
    frames_dir = FRAMES_DIR.parent / "pilot8" if args.smoke else FRAMES_DIR
    frames = sorted(frames_dir.glob("venus-loop-*.png")) if args.smoke else [
        FRAMES_DIR / f"venus-loop-{frame:03d}.png" for frame in range(1, 301)
    ]
    output = REPORT.parent / "encode-smoke.mp4" if args.smoke else OUTPUT
    report_path = REPORT.parent / "encode-smoke-report.json" if args.smoke else REPORT
    if args.smoke and len(frames) != 4:
        raise RuntimeError(f"Expected four pilot frames, found {len(frames)}")
    missing = [path.name for path in frames if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} rendered frames; first missing: {missing[:8]}")
    bad_sizes = [path.name for path in frames if image_dimensions(path) != (1280, 720)]
    if bad_sizes:
        raise RuntimeError(f"Wrong PNG dimensions: {bad_sizes[:8]}")
    if output.exists():
        raise RuntimeError(f"Output already exists; refusing to overwrite: {output}")

    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    # The PNGs already contain the v17 scene's AgX look. Preserve those display
    # colors when reading them back through the video sequencer.
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.frame_start = 1
    scene.frame_end = len(frames)
    editor = scene.sequence_editor_create()
    strip = editor.sequences.new_image("Venus 720p preview", str(frames[0]), channel=1, frame_start=1)
    for frame in frames[1:]:
        strip.elements.append(frame.name)
    if strip.frame_final_end != len(frames) + 1:
        raise RuntimeError(f"Unexpected image-strip end: {strip.frame_final_end}")

    scene.render.use_sequencer = True
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.audio_codec = "NONE"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.gopsize = 30
    scene.render.filepath = str(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not args.smoke:
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(EDIT_BLEND))

    started = time.perf_counter()
    print(json.dumps({"stage": "encode_start", "frames": len(frames), "output": str(output)}), flush=True)
    bpy.ops.render.render(animation=True)
    elapsed = round(time.perf_counter() - started, 3)
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"Blender did not write the MP4: {output}")
    report = {
        "source_frames": str(frames_dir),
        "frame_count": len(frames),
        "resolution": [1280, 720],
        "fps": 30,
        "codec": "H264",
        "quality": "MEDIUM",
        "output": str(output),
        "bytes": output.stat().st_size,
        "encode_seconds": elapsed,
        "edit_blend": str(EDIT_BLEND) if not args.smoke else None,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"stage": "encode_complete", **report}), flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    raise
