"""Validate all final PNGs, representative phases, and the 300→1 loop seam."""

import json
from pathlib import Path

import numpy as np
from PIL import Image


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
FRAMES_DIR = PROJECT / "renders" / "frames" / "venus-final-1080p"
REPORT = PROJECT / "output" / "venus-restoration-v17-final-validation.json"
EXPECTED = [FRAMES_DIR / f"venus-final-{frame:03d}.png" for frame in range(1, 301)]


def rgb(path):
    with Image.open(path) as image:
        if image.size != (1920, 1080):
            raise RuntimeError(f"Wrong frame dimensions: {path} {image.size}")
        return np.asarray(image.convert("RGB"), dtype=np.int16)


def delta(first, second):
    return round(float(np.abs(first - second).mean() / 255.0), 7)


def main():
    missing = [path.name for path in EXPECTED if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} final frames; first: {missing[:8]}")
    extras = sorted(path.name for path in FRAMES_DIR.glob("venus-final-*.png") if path not in EXPECTED)
    if extras:
        raise RuntimeError(f"Unexpected frame files: {extras[:8]}")

    first = rgb(EXPECTED[0])
    previous = first
    adjacent = []
    for frame, path in enumerate(EXPECTED[1:], start=2):
        current = rgb(path)
        adjacent.append({"from": frame - 1, "to": frame, "mean_abs": delta(previous, current)})
        previous = current
    seam = delta(previous, first)
    ordinary = np.asarray([entry["mean_abs"] for entry in adjacent])
    phases = {str(frame): delta(first, rgb(EXPECTED[frame - 1])) for frame in (1, 76, 151, 226)}
    report = {
        "frame_count": 300,
        "resolution": [1920, 1080],
        "fps": 30,
        "loop_seam_300_to_1_mean_abs": seam,
        "ordinary_adjacent_median_mean_abs": round(float(np.median(ordinary)), 7),
        "ordinary_adjacent_p95_mean_abs": round(float(np.percentile(ordinary, 95)), 7),
        "seam_rank_among_300_transitions": int(np.count_nonzero(ordinary <= seam)) + 1,
        "phase_delta_from_1": phases,
        "largest_ordinary_transitions": sorted(adjacent, key=lambda entry: entry["mean_abs"], reverse=True)[:8],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
