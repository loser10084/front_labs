"""Convert final PNG frames to a browser-friendly WebP sequence for Canvas scrubbing."""

import json
import time
from pathlib import Path

from PIL import Image


PROJECT = Path(r"D:\project\AI\frontend_labs\labs_2\blender-loop-video")
SOURCE = PROJECT / "renders" / "frames" / "venus-final-1080p"
OUTPUT = (
    PROJECT
    / "web-showcase"
    / "prototypes"
    / "continuous-video-v2-1080p"
    / "assets"
    / "scroll-frames"
)
REPORT = PROJECT / "output" / "venus-scroll-frames-webp-report.json"
FRAMES = [SOURCE / f"venus-final-{frame:03d}.png" for frame in range(1, 301)]


def main() -> None:
    missing = [path.name for path in FRAMES if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} source frames; first: {missing[:8]}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    existing = list(OUTPUT.glob("frame-*.webp"))
    if existing:
        raise RuntimeError(f"Output already contains {len(existing)} WebP frames: {OUTPUT}")

    started = time.perf_counter()
    written = []
    for index, source in enumerate(FRAMES, start=1):
        target = OUTPUT / f"frame-{index:03d}.webp"
        with Image.open(source) as image:
            image.save(target, "WEBP", quality=88, method=4)
        written.append(target)
        if index == 1 or index % 50 == 0:
            print(json.dumps({"stage": "webp_frame", "frame": index}), flush=True)

    report = {
        "source": str(SOURCE),
        "output": str(OUTPUT),
        "frame_count": len(written),
        "resolution": [1920, 1080],
        "quality": 88,
        "bytes": sum(path.stat().st_size for path in written),
        "seconds": round(time.perf_counter() - started, 3),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"stage": "webp_complete", **report}), flush=True)


if __name__ == "__main__":
    main()
