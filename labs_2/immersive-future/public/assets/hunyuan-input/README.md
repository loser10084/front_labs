# Hunyuan 3D input guide

These images are isolated modeling references for Hunyuan `图生3D`. They are
not website posters. Keep the original PNG files unchanged when uploading.

## Recommended settings

| Asset | Mode | Model | Face count | Upload order | Status |
| --- | --- | --- | --- | --- | --- |
| Orbital ring | 图生3D / 多张图片 | 3D生成 V3.1 | 1.5m | views `01` → `04` | Ready (4 views) |
| Bio drone | 图生3D / 多张图片 | 3D生成 V3.1 | 500k | views `01` → `04` | Ready (4 views) |
| Data flora | 图生3D / 多张图片 | 3D生成 V3.1 | 1m | views `01` → `04` | Ready (4 views) |

## Why these face counts

- **Orbital ring — 1.5m:** repeated windows, garden terraces, radial bridges,
  pylons and underside service geometry need the highest available budget.
- **Bio drone — 500k:** the silhouette and membrane segmentation matter more
  than dense surface tessellation; 500k is enough for a background fly-through.
- **Data flora — 1m:** thin stems, hinge joints, conduits and overlapping leaf
  plates need more geometry than the drone, but not the full architectural budget.

Do not use `50k` for final generation. It is suitable only for a rough preview.

## Upload rules

1. Select `图生3D` → `多张图片`.
2. Keep model `3D生成 V3.1`.
3. Upload only images from one asset folder in a generation job.
4. Do not mix website hero/poster images with the isolated modeling views.
5. Keep the object orientation and material language; generate materials if the
   Hunyuan result offers a textured/PBR export option.
6. Export GLB with textures embedded. Do not decimate during the first export;
   create web LODs only after visual approval.

## View sets

- `orbital-ring`: front three-quarter, top, rear underside, side profile.
- `bio-drone`: front three-quarter, top, rear underside, right profile.
- `data-flora`: front three-quarter, right profile, rear three-quarter, left profile.

Upload all four images in filename order. If Hunyuan reports conflicting-view
geometry, keep views `01`, `02`, and `04`; view `03` is the first one to remove.

## Intended replacement files

After approval, keep the generated sources versioned and export web-ready files
as new assets first:

- `models/orbital-ring-hunyuan-v1.glb`
- `models/bio-drone-hunyuan-v1.glb`
- `models/data-flora-hunyuan-v1.glb`

Do not overwrite the current prototypes until the new files pass browser and
mobile performance checks.
