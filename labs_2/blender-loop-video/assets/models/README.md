# 维纳斯模型资产

## 源模型

- `source/venus-hunyuan-v1.glb`
- 由用户提供的混元成品复制而来，项目副本与下载原件 SHA-256 一致。
- 不直接覆盖或破坏该文件。

## Blender 修订版本

修改后的自包含模型位于 `../../blend/venus-restoration-v07-review.blend`。三张 4096 × 4096 贴图已经打包进 `.blend`。

主要调整：

- 世界空间高度规范为 3.4 m。
- 原模型形象和衣褶保留，不做无依据重塑。
- 重建大理石、黑曜石、烟熏树脂与金属连接件的 Blender 材质响应。
- 增加可整体隐藏的 `VENUS_PRESENTATION` 博物馆基座集合。

当前没有导出“修订版 GLB”，因为 Blender 原生混合着色需要先烘焙为标准 glTF PBR 贴图；未烘焙直接导出会产生错误交付。
