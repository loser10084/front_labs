"""Check all 300 preview PNGs and compare the loop seam with ordinary cuts."""

import json
from pathlib import Path

import numpy as np
from PIL import Image


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
FRAMES_DIR = PROJECT / "renders" / "previews" / "cinematic-loop-720p" / "frames"
REPORT = FRAMES_DIR.parent / "loop-validation.json"
EXPECTED = [FRAMES_DIR / f"venus-loop-{frame:03d}.png" for frame in range(1, 301)]


def load_rgb(path):
    with Image.open(path) as image:
        if image.size != (1280, 720):
            raise RuntimeError(f"Wrong dimensions: {path} {image.size}")
        return np.asarray(image.convert("RGB"), dtype=np.int16)


def mean_delta(first, second):
    return round(float(np.abs(first - second).mean() / 255.0), 7)


def main():
    missing = [path.name for path in EXPECTED if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} frames; first: {missing[:8]}")
    extras = sorted(path.name for path in FRAMES_DIR.glob("venus-loop-*.png") if path not in EXPECTED)
    if extras:
        raise RuntimeError(f"Unexpected frame names: {extras[:8]}")

    first = load_rgb(EXPECTED[0])
    previous = first
    deltas = []
    for frame, path in enumerate(EXPECTED[1:], start=2):
        current = load_rgb(path)
        deltas.append({"from": frame - 1, "to": frame, "mean_abs": mean_delta(previous, current)})
        previous = current
    seam = mean_delta(previous, first)
    ordinary = np.asarray([item["mean_abs"] for item in deltas])
    keyframes = [1, 76, 151, 226]
    keyframe_deltas = {
        str(frame): mean_delta(first, load_rgb(EXPECTED[frame - 1]))
        for frame in keyframes
    }
    report = {
        "frame_count": len(EXPECTED),
        "resolution": [1280, 720],
        "frame_1_vs_300_mean_abs": seam,
        "adjacent_median_mean_abs": round(float(np.median(ordinary)), 7),
        "adjacent_p95_mean_abs": round(float(np.percentile(ordinary, 95)), 7),
        "adjacent_max_mean_abs": round(float(np.max(ordinary)), 7),
        "seam_rank_among_300_transitions": int(np.count_nonzero(ordinary <= seam)) + 1,
        "keyframe_delta_from_1": keyframe_deltas,
        "largest_ordinary_transitions": sorted(deltas, key=lambda item: item["mean_abs"], reverse=True)[:8],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
