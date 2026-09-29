"""Measure color and compression drift between rendered and encoded frames."""

import json
from pathlib import Path

import numpy as np
from PIL import Image


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
BASE = PROJECT / "renders" / "previews" / "cinematic-loop-720p"
REPORT = BASE / "encoded-frame-comparison.json"
FRAMES = (1, 76, 151, 226, 300)


def pixels(path):
    with Image.open(path) as image:
        if image.size != (1280, 720):
            raise RuntimeError(f"Unexpected image dimensions: {path} {image.size}")
        return np.asarray(image.convert("RGB"), dtype=np.int16)


def main():
    comparisons = []
    for frame in FRAMES:
        original = pixels(BASE / "frames" / f"venus-loop-{frame:03d}.png")
        encoded = pixels(BASE / "encoded-check" / f"encoded-{frame:03d}.png")
        difference = encoded - original
        comparisons.append({
            "frame": frame,
            "mean_absolute_rgb_255": round(float(np.abs(difference).mean()), 4),
            "mean_channel_shift_rgb_255": [
                round(float(value), 4) for value in difference.mean(axis=(0, 1))
            ],
        })
    report = {
        "frames_compared": list(FRAMES),
        "comparisons": comparisons,
        "mean_absolute_rgb_255": round(float(np.mean([
            item["mean_absolute_rgb_255"] for item in comparisons
        ])), 4),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
