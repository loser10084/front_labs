# GLB prototype assets

Generated with Blender 4.2.16 LTS through Blender MCP on 2026-09-20. All three assets use procedural geometry and project-local PBR materials; no external model downloads were used.

These prototypes are low-poly GLB files without Draco mesh compression. Their only declared glTF extension is `KHR_materials_emissive_strength` for the orange signal material.

| File | Root node | Meshes | Triangles | Bounds | Size |
| --- | --- | ---: | ---: | --- | ---: |
| `orbital-ring.glb` | `FW_OrbitalRing_ROOT` | 55 | 15,944 | 9.32 × 9.32 × 3.915m | 636,132 bytes |
| `bio-drone.glb` | `FW_BioDrone_ROOT` | 13 | 2,204 | 5.212 × 4.09 × 0.774m | 111,740 bytes |
| `data-flora.glb` | `FW_DataFlora_ROOT` | 33 | 6,468 | 3.34 × 3.639 × 3.14m | 320,096 bytes |

## Materials

- `FW_CeramicWhite`: matte pale ceramic structure.
- `FW_Graphite`: dark metallic rails and structural details.
- `FW_GardenPale`: restrained green ecological surfaces.
- `FW_SignalOrange`: emissive orange navigation accents.

## Intended use

- `orbital-ring.glb`: hero background and Gateway chapter.
- `bio-drone.glb`: Manifesto chapter fly-through object.
- `data-flora.glb`: Protocol chapter foreground/background relief.

The models are static prototypes with no armature or baked animation. Animation should be applied in Three.js/GSAP through root-node transforms; future animated revisions should use new filenames rather than silently replacing these prototypes.

## Verification

Each exported GLB was re-imported into Blender with `bpy.ops.import_scene.gltf`. Root nodes, mesh counts, material usage and polygon counts were checked after re-import, then the temporary verification objects were removed.
