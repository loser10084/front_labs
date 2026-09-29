# Codex + Blender：10 秒无缝循环背景视频实验

这是一个独立于 `immersive-future` 的新实验。实验只验证一件事：Codex 能否通过 Blender 建景、材质、灯光、动画、渲染和编码，产出一个符合人工视觉预期、可用于网页背景的高质量 10 秒无缝循环视频。

详细制作方案见 [`production-plan.md`](production-plan.md)。

## 当前状态

- 实验目录已建立。
- 固定交付规格、流动雕塑艺术方向和无缝循环策略已确定。
- 预览锁定为 1280 × 720，目标渲染时间 5–10 分钟。
- 最终成片锁定为 1920 × 1080、30 fps、Eevee 优先，目标渲染时间 30–90 分钟。
- Gate 0 已完成：Blender 4.2.16 LTS 与 MCP 协议 9 连接正常，插件状态为最新，遥测关闭。
- 独立工程已保存为 `blend/liquid-monument-v01.blend`。
- 场景已设置为 Eevee、1920 × 1080、30 fps、1–300 帧、AgX，并将第 301 帧记录为循环校验帧。
- 第一版抽象带状雕塑灰模未通过视觉验收：主体含义不清，环绕棍状碎片缺少叙事依据，已停止继续加工。
- 新方向锁定为“未来考古修复的断臂古典女神像”：雕像穿一体雕刻的高领及踝石质长袍，以断臂、古典面容与站姿建立识别。
- 标准断臂维纳斯 v3 六视图已完成：正面、前左 45°、左侧 90°、背面 180°、右侧 90°、前右 45°；非大理石修复材质约占 60%。
- 混元成品 GLB 已作为只读源资产保存到 `assets/models/source/venus-hunyuan-v1.glb`，原下载文件未改动。
- Blender 修订候选已保存为 `blend/venus-restoration-v07-review.blend`：规范为 3.4 m 高，重建多材质节点，保留 4K 基础色/金属粗糙度/法线贴图，并增加可隐藏的低矮黑色博物馆基座。
- 模型验收图位于 `renders/previews/venus-final-review/`。
- 正式博物馆装置灰模已保存为 `blend/venus-restoration-v08-museum-gate.blend`：雕像位于右侧并允许局部出框，左侧保留低细节文字区。
- 周期动效关卡已保存为 `blend/venus-restoration-v09-motion-gate.blend`：300 帧闭合相机、低能量扫描光、低密度体积层和 18 个克制尘埃实例。
- 最终材质母版为 `blend/venus-restoration-v15-clean-resin.blend`；面部使用低强度独立法线，黑曜石与烟熏树脂使用修订后的语义遮罩。
- 最终材质动画关卡为 `blend/venus-restoration-v16-final-material-motion-gate.blend`；24 个早期 Ribbon/Trace/Shard 遗留对象已隐藏。
- 最终材质版第 1/301 帧的相机、目标、扫描灯和抽样尘埃状态完全一致；921,600 个像素中仅 3 个像素差值大于 1。
- 新镜头叙事版为 `blend/venus-restoration-v17-cinematic-camera.blend`；分镜预览在 `renders/previews/cinematic-motion-storyboard/`，从展厅全景推进到面部、材质和衣袍细节，再回到全景。
- v17 的第 1/301 帧相机、焦点与焦距完全一致；像素差为 89/921,600，最大通道差 2/255。已匹配闭环相机曲线切线。
- `blender.exe`、`ffmpeg.exe`、`ffprobe.exe` 当前不在终端 PATH。
- 第一版优先使用 Blender 自带 FFmpeg 编码，不依赖外部 FFmpeg。
- 720p、30 FPS、300 帧预览已完成：`output/venus-restoration-v17-preview-720p.mp4`，H.264，10.000 秒，约 3.31 MB；封面为 `output/venus-restoration-v17-poster-720p.png`。
- 编码时保持原 PNG 的显示色彩；从成片解码抽查五帧，与渲染 PNG 的平均 RGB 绝对差为 2.18/255。
- 预览使用 Eevee 8 次采样，300 帧实际耗时 953 秒，超过 5–10 分钟目标；近景颗粒应在最终质量关卡继续检查。
- 第 300→1 帧的平均像素变化低于普通相邻帧中位数；循环实际播放观感仍需人工观看确认。
- 1080p、30 FPS、300 帧高画质成片已完成：`output/venus-restoration-v17-final-1080p.mp4`，Eevee 32 次采样、H.264 HIGH 档，约 7.16 MB；海报为 `output/venus-restoration-v17-final-poster-1080p.png`。
- 1080p PNG 母版位于 `renders/frames/venus-final-1080p/`，300 帧渲染耗时约 66 分钟。第 300→1 帧平均变化 0.0132，低于普通相邻帧中位数 0.0214；编码视频关键帧与 PNG 平均 RGB 绝对差约 1.84/255。
- 独立的 [VENUS RECONSTRUCTED 网页展示](web-showcase/README.md)已切换至 1080p 最终视频与同分辨率剧照，包含桌面/移动布局、播放控制及细节切换。

## 目录

```text
blender-loop-video/
├─ README.md
├─ production-plan.md
├─ blend/                 # .blend 工程
├─ scripts/               # Codex 通过 Blender MCP 执行或保存的 bpy 脚本
├─ renders/
│  ├─ frames/             # 最终 PNG 帧序列
│  └─ previews/           # 低分辨率预览和校验帧
└─ output/                # 最终 MP4/WebM 与 poster
```

## 下一步入口

1. 在目标浏览器中连续播放 `output/venus-restoration-v17-final-1080p.mp4` 至少 5 次，人工确认镜头节奏、近景纹理和循环接缝。
2. 如需其他码率或格式，可直接使用 `renders/frames/venus-final-1080p/` 的 PNG 母版重新编码，无需重渲 3D 场景。

执行证据见 [`experiment-log.md`](experiment-log.md)。
