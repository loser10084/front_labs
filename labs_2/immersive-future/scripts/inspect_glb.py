from __future__ import annotations

import json
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "public" / "assets" / "models"


def inspect(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        raise ValueError(f"Not a GLB file: {path}")

    version, declared_length = struct.unpack_from("<II", data, 4)
    json_length, json_type = struct.unpack_from("<II", data, 12)
    if json_type != 0x4E4F534A:
        raise ValueError(f"First GLB chunk is not JSON: {path}")

    document = json.loads(data[20 : 20 + json_length].decode("utf-8").rstrip(" \x00"))
    return {
        "file": path.name,
        "bytes": len(data),
        "declared_length": declared_length,
        "version": version,
        "scenes": len(document.get("scenes", [])),
        "nodes": len(document.get("nodes", [])),
        "meshes": len(document.get("meshes", [])),
        "materials": len(document.get("materials", [])),
        "extensions_used": document.get("extensionsUsed", []),
        "valid_length": declared_length == len(data),
    }


def main() -> None:
    paths = sorted(MODELS.glob("*.glb"))
    if not paths:
        raise FileNotFoundError(f"No GLB files found in {MODELS}")
    for path in paths:
        print(json.dumps(inspect(path), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
