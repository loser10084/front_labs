"""Render selected v17 frames or the full 720p loop as resumable PNGs.

Usage:
  blender --background <v17.blend> --python <this file> -- --samples 8 --frames 38,114
  blender --background <v17.blend> --python <this file> -- --samples 8 --frames 1-300 --resume
"""

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

import bpy


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
SOURCE_NAME = "venus-restoration-v17-cinematic-camera.blend"
EXPECTED_MATERIAL = "VENUS_Restoration_Material_v9_CleanResin"


def parse_frames(value):
    frames = set()
    for part in value.split(","):
        token = part.strip()
        if "-" in token:
            first, last = (int(text) for text in token.split("-", 1))
            frames.update(range(first, last + 1))
        else:
            frames.add(int(token))
    if not frames or min(frames) < 1 or max(frames) > 300:
        raise argparse.ArgumentTypeError("Frame selection must be within 1–300")
    return sorted(frames)


def complete_png(path):
    if not path.is_file() or path.stat().st_size < 1000:
        return False
    with path.open("rb") as handle:
        handle.seek(-12, 2)
        return handle.read() == b"\x00\x00\x00\x00IEND\xaeB\x60\x82"


def write_report(path, report):
    temp_path = path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--frames", type=parse_frames, default=parse_frames("1-300"))
    parser.add_argument("--output-dir", type=Path, default=Path("renders/previews/cinematic-loop-720p/frames"))
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)

    if args.samples < 1 or args.samples > 64:
        raise ValueError("Preview samples must be within 1–64")
    if Path(bpy.data.filepath).name != SOURCE_NAME:
        raise RuntimeError(f"Expected {SOURCE_NAME}, got {bpy.data.filepath}")

    scene = bpy.context.scene
    statue = bpy.data.objects.get("VENUS_Hunyuan_Working")
    if scene.camera is None or scene.camera.name != "VENUS_Hall_Camera":
        raise RuntimeError("VENUS_Hall_Camera is not the active scene camera")
    if statue is None or statue.active_material is None or statue.active_material.name != EXPECTED_MATERIAL:
        raise RuntimeError("The final Venus mesh/material is missing")

    output_dir = args.output_dir if args.output_dir.is_absolute() else PROJECT / args.output_dir
    output_dir = output_dir.resolve()
    if not output_dir.is_relative_to(PROJECT.resolve()):
        raise ValueError(f"Output directory is outside the experiment: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = args.samples
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15

    report_path = output_dir.parent / f"{output_dir.name}-render-report.json"
    previous_frames = {}
    if args.resume and report_path.exists():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        if (
            previous.get("source_blend") != bpy.data.filepath
            or previous.get("samples") != args.samples
            or previous.get("resolution") != [1280, 720]
            or previous.get("fps") != 30
        ):
            raise RuntimeError(f"Cannot resume with different source or render settings: {report_path}")
        previous_frames = previous.get("frames", {})
    report = {
        "source_blend": bpy.data.filepath,
        "output_dir": str(output_dir),
        "resolution": [1280, 720],
        "fps": 30,
        "samples": args.samples,
        "requested_frames": args.frames,
        "status": "running",
        "frames": previous_frames,
    }
    started_all = time.perf_counter()
    write_report(report_path, report)

    try:
        for frame in args.frames:
            path = output_dir / f"venus-loop-{frame:03d}.png"
            if args.resume and complete_png(path):
                report["frames"][str(frame)] = {"status": "skipped_existing", "bytes": path.stat().st_size}
                print(json.dumps({"stage": "render", "frame": frame, "status": "skipped_existing"}), flush=True)
                continue
            scene.frame_set(frame)
            scene.render.filepath = str(path)
            started = time.perf_counter()
            bpy.ops.render.render(write_still=True)
            if not complete_png(path):
                raise RuntimeError(f"Rendered PNG is missing or incomplete: {path}")
            elapsed = round(time.perf_counter() - started, 3)
            report["frames"][str(frame)] = {"status": "rendered", "seconds": elapsed, "bytes": path.stat().st_size}
            write_report(report_path, report)
            print(json.dumps({"stage": "render", "frame": frame, "seconds": elapsed, "samples": args.samples}), flush=True)
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = {"frame": frame, "type": type(exc).__name__, "message": str(exc)}
        write_report(report_path, report)
        raise

    report["status"] = "complete"
    report["elapsed_seconds"] = round(time.perf_counter() - started_all, 3)
    write_report(report_path, report)
    print(json.dumps({"stage": "complete", "frames": len(args.frames), "elapsed_seconds": report["elapsed_seconds"], "report": str(report_path)}), flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    raise
