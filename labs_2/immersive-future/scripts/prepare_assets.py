from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "public" / "assets"


@dataclass(frozen=True)
class Conversion:
    source: Path
    target: Path
    max_bytes: int
    start_quality: int = 86
    preserve_alpha: bool = False


CONVERSIONS = (
    Conversion(
        ASSETS / "hero" / "orbital-gateway-master.png",
        ASSETS / "hero" / "orbital-gateway.webp",
        700_000,
    ),
    Conversion(
        ASSETS / "posters" / "project-01-orbital-habitat.png",
        ASSETS / "posters" / "project-01-orbital-habitat.webp",
        500_000,
    ),
    Conversion(
        ASSETS / "posters" / "project-02-synthetic-forest.png",
        ASSETS / "posters" / "project-02-synthetic-forest.webp",
        500_000,
    ),
    Conversion(
        ASSETS / "posters" / "project-03-lunar-archive.png",
        ASSETS / "posters" / "project-03-lunar-archive.webp",
        500_000,
    ),
    Conversion(
        ASSETS / "posters" / "project-04-ocean-colony.png",
        ASSETS / "posters" / "project-04-ocean-colony.webp",
        500_000,
    ),
    Conversion(
        ASSETS / "textures" / "concrete-cool-master.png",
        ASSETS / "textures" / "concrete-cool.webp",
        450_000,
        82,
    ),
    Conversion(
        ASSETS / "backdrops" / "relief-orbital-ring.png",
        ASSETS / "backdrops" / "relief-orbital-ring.webp",
        500_000,
        82,
        True,
    ),
    Conversion(
        ASSETS / "backdrops" / "relief-bio-drone.png",
        ASSETS / "backdrops" / "relief-bio-drone.webp",
        420_000,
        82,
        True,
    ),
    Conversion(
        ASSETS / "backdrops" / "relief-data-flora.png",
        ASSETS / "backdrops" / "relief-data-flora.webp",
        420_000,
        82,
        True,
    ),
    Conversion(
        ASSETS / "backdrops" / "lunar-ocean-transition-master.png",
        ASSETS / "backdrops" / "lunar-ocean-transition.webp",
        500_000,
        82,
    ),
)


def convert_webp(job: Conversion) -> None:
    if not job.source.is_file():
        raise FileNotFoundError(f"Missing source asset: {job.source}")

    job.target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(job.source) as source:
        image = source.convert("RGBA" if job.preserve_alpha else "RGB")
        quality = job.start_quality
        while True:
            image.save(
                job.target,
                "WEBP",
                quality=quality,
                method=6,
                exact=job.preserve_alpha,
            )
            size = job.target.stat().st_size
            if size <= job.max_bytes or quality <= 58:
                break
            quality -= 4

        print(
            f"converted source={job.source.relative_to(ROOT)} "
            f"target={job.target.relative_to(ROOT)} dimensions={image.size} "
            f"quality={quality} bytes={size} budget={job.max_bytes}"
        )

        if size > job.max_bytes:
            raise RuntimeError(
                f"Asset exceeds budget after compression: {job.target} "
                f"({size} > {job.max_bytes})"
            )


def create_noise_texture() -> None:
    target = ASSETS / "textures" / "noise-64.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    randomizer = random.Random(20260920)
    image = Image.new("L", (64, 64))
    image.putdata([randomizer.randint(218, 236) for _ in range(64 * 64)])
    image.save(target, "PNG", optimize=True)
    print(
        f"generated target={target.relative_to(ROOT)} dimensions={image.size} "
        f"bytes={target.stat().st_size} seed=20260920"
    )


def validate_aspect_ratios() -> None:
    visual_sources = [
        job.source
        for job in CONVERSIONS
        if "textures" not in job.source.parts and not job.preserve_alpha
    ]
    for source in visual_sources:
        with Image.open(source) as image:
            ratio = image.width / image.height
        if abs(ratio - (16 / 9)) > 0.01:
            raise RuntimeError(
                f"Expected a 16:9 visual asset: {source} has ratio {ratio:.4f}"
            )
        print(
            f"validated source={source.relative_to(ROOT)} "
            f"aspect={ratio:.4f} expected={16 / 9:.4f}"
        )


def main() -> None:
    validate_aspect_ratios()
    for conversion in CONVERSIONS:
        convert_webp(conversion)
    create_noise_texture()


if __name__ == "__main__":
    main()
