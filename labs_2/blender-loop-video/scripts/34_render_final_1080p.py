"""Render the locked v17 camera loop as resumable 1080p PNG frames.

Usage:
  blender --background <v17.blend> --python <this file> -- --frames 151 --samples 32
  blender --background <v17.blend> --python <this file> -- --frames 1-300 --samples 32 --resume
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
OUTPUT_DIR = PROJECT / "renders" / "frames" / "venus-final-1080p"
REPORT = OUTPUT_DIR.parent / "venus-final-1080p-render-report.json"
RESOLUTION = [1920, 1080]


def parse_frames(value):
    frames = set()
    for part in value.split(","):
        token = part.strip()
        if "-" in token:
            first, last = (int(item) for item in token.split("-", 1))
            frames.update(range(first, last + 1))
        else:
            frames.add(int(token))
    if not frames or min(frames) < 1 or max(frames) > 300:
        raise argparse.ArgumentTypeError("Frames must be within 1–300")
    return sorted(frames)


def complete_png(path):
    if not path.is_file() or path.stat().st_size < 1000:
        return False
    with path.open("rb") as stream:
        stream.seek(-12, 2)
        return stream.read() == b"\x00\x00\x00\x00IEND\xaeB\x60\x82"


def write_report(report):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    temp = REPORT.with_suffix(".json.tmp")
    temp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(REPORT)


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=parse_frames, default=parse_frames("1-300"))
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    if args.samples < 16 or args.samples > 64:
        raise ValueError("Final samples must be within 16–64")
    if Path(bpy.data.filepath).name != SOURCE_NAME:
        raise RuntimeError(f"Expected {SOURCE_NAME}, got {bpy.data.filepath}")

    scene = bpy.context.scene
    statue = bpy.data.objects.get("VENUS_Hunyuan_Working")
    if scene.camera is None or scene.camera.name != "VENUS_Hall_Camera":
        raise RuntimeError("VENUS_Hall_Camera is not the active camera")
    if statue is None or statue.active_material is None or statue.active_material.name != EXPECTED_MATERIAL:
        raise RuntimeError("The locked final Venus mesh/material is missing")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = args.samples
    scene.render.resolution_x, scene.render.resolution_y = RESOLUTION
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15

    previous_frames = {}
    if REPORT.exists():
        previous = json.loads(REPORT.read_text(encoding="utf-8"))
        expected = (str(PROJECT / "blend" / SOURCE_NAME), RESOLUTION, 30, args.samples)
        recorded = (
            previous.get("source_blend"), previous.get("resolution"),
            previous.get("fps"), previous.get("samples"),
        )
        if recorded != expected:
            raise RuntimeError(f"Render settings differ from existing report: {recorded}")
        if not args.resume:
            raise RuntimeError(f"Existing render report requires --resume: {REPORT}")
        previous_frames = previous.get("frames", {})

    report = {
        "source_blend": bpy.data.filepath,
        "output_dir": str(OUTPUT_DIR),
        "resolution": RESOLUTION,
        "fps": 30,
        "samples": args.samples,
        "requested_frames": args.frames,
        "status": "running",
        "frames": previous_frames,
    }
    started_all = time.perf_counter()
    write_report(report)
    frame = None
    try:
        for frame in args.frames:
            path = OUTPUT_DIR / f"venus-final-{frame:03d}.png"
            if args.resume and complete_png(path):
                report["frames"][str(frame)] = {"status": "skipped_existing", "bytes": path.stat().st_size}
                print(json.dumps({"stage": "render", "frame": frame, "status": "skipped_existing"}), flush=True)
                continue
            if path.exists():
                raise RuntimeError(f"Existing incomplete frame must be inspected before overwriting: {path}")
            scene.frame_set(frame)
            scene.render.filepath = str(path)
            started = time.perf_counter()
            bpy.ops.render.render(write_still=True)
            if not complete_png(path):
                raise RuntimeError(f"Rendered PNG is missing or incomplete: {path}")
            seconds = round(time.perf_counter() - started, 3)
            report["frames"][str(frame)] = {"status": "rendered", "seconds": seconds, "bytes": path.stat().st_size}
            write_report(report)
            print(json.dumps({"stage": "render", "frame": frame, "seconds": seconds, "samples": args.samples}), flush=True)
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = {"frame": frame, "type": type(exc).__name__, "message": str(exc)}
        write_report(report)
        raise

    report["status"] = "complete" if len(report["frames"]) == 300 else "partial"
    report["elapsed_seconds"] = round(time.perf_counter() - started_all, 3)
    write_report(report)
    print(json.dumps({"stage": report["status"], "frames": len(report["frames"]), "elapsed_seconds": report["elapsed_seconds"]}), flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    raise
