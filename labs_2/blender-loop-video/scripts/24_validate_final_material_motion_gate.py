"""Validate image and state closure for the final-material motion gate."""

from pathlib import Path
import json

import numpy as np
from PIL import Image


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
OUTPUT_DIR = PROJECT / "renders" / "previews" / "final-material-motion-gate"
STATE_PATH = OUTPUT_DIR / "motion-gate-state.json"
VALIDATION_PATH = OUTPUT_DIR / "motion-gate-validation.json"


def maximum_delta(left, right):
    if isinstance(left, dict):
        return max((maximum_delta(left[key], right[key]) for key in left if key in right), default=0.0)
    if isinstance(left, list):
        return max((maximum_delta(a, b) for a, b in zip(left, right)), default=0.0)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right))
    return 0.0 if left == right else float("inf")


def main():
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    states = {entry["frame"]: entry for entry in state["states"]}
    first = states[1]
    last = states[301]

    image_1 = np.asarray(Image.open(first["output"]).convert("RGB"), dtype=np.int16)
    image_301 = np.asarray(Image.open(last["output"]).convert("RGB"), dtype=np.int16)
    diff = np.abs(image_1 - image_301)

    bounds = [entry["statue_screen_bounds"] for entry in state["states"]]
    result = {
        "state_loop_max_delta": maximum_delta(
            {key: first[key] for key in ["camera", "camera_lens", "camera_target", "statue_screen_bounds", "scan_light", "dust_sample", "material"]},
            {key: last[key] for key in ["camera", "camera_lens", "camera_target", "statue_screen_bounds", "scan_light", "dust_sample", "material"]},
        ),
        "pixel_loop": {
            "mean_abs_rgb": [round(float(value), 8) for value in diff.mean(axis=(0, 1))],
            "mean_abs_all": round(float(diff.mean()), 8),
            "max_abs": int(diff.max()),
            "pixels_over_1": int(np.count_nonzero(np.max(diff, axis=2) > 1)),
            "pixels_over_5": int(np.count_nonzero(np.max(diff, axis=2) > 5)),
            "total_pixels": int(diff.shape[0] * diff.shape[1]),
        },
        "composition": {
            "statue_x_min_range": [min(item["x_min"] for item in bounds), max(item["x_min"] for item in bounds)],
            "statue_x_max_range": [min(item["x_max"] for item in bounds), max(item["x_max"] for item in bounds)],
            "statue_y_min_range": [min(item["y_min"] for item in bounds), max(item["y_min"] for item in bounds)],
            "statue_y_max_range": [min(item["y_max"] for item in bounds), max(item["y_max"] for item in bounds)],
            "left_clear_fraction_min": min(item["x_min"] for item in bounds),
            "right_margin_fraction_min": 1.0 - max(item["x_max"] for item in bounds),
        },
        "render_seconds": {
            "per_frame": {str(entry["frame"]): entry["render_seconds"] for entry in state["states"]},
            "total": round(sum(entry["render_seconds"] for entry in state["states"]), 3),
        },
    }
    VALIDATION_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
