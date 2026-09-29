"""Measure H.264 color/compression drift against the final PNG frames."""

import json
from pathlib import Path

import numpy as np
from PIL import Image


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
ORIGINAL = PROJECT / "renders" / "frames" / "venus-final-1080p"
DECODED = PROJECT / "renders" / "previews" / "final-encoded-check-1080p"
REPORT = PROJECT / "output" / "venus-restoration-v17-final-encoded-comparison.json"
FRAMES = (1, 76, 151, 226, 300)


def rgb(path):
    with Image.open(path) as image:
        if image.size != (1920, 1080):
            raise RuntimeError(f"Unexpected dimensions: {path} {image.size}")
        return np.asarray(image.convert("RGB"), dtype=np.int16)


def main():
    comparisons = []
    for frame in FRAMES:
        original = rgb(ORIGINAL / f"venus-final-{frame:03d}.png")
        encoded = rgb(DECODED / f"decoded-{frame:03d}.png")
        difference = encoded - original
        comparisons.append({
            "frame": frame,
            "mean_absolute_rgb_255": round(float(np.abs(difference).mean()), 4),
            "mean_channel_shift_rgb_255": [round(float(value), 4) for value in difference.mean(axis=(0, 1))],
        })
    report = {
        "frames_compared": list(FRAMES),
        "comparisons": comparisons,
        "mean_absolute_rgb_255": round(float(np.mean([entry["mean_absolute_rgb_255"] for entry in comparisons])), 4),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
