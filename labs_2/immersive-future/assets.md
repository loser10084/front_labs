# 未来世界官网复刻：素材分析与替代计划

> 目标是理解参考站的素材角色和技术形态，再制作独立的“未来世界”素材。原站品牌资源只用于分析，不进入最终项目。

## 1. 浏览器取证摘要

在 1440 × 1000 与 390 × 844 真实浏览器会话中观察到：

- DOM 中存在 12 个 `canvas`、39 个透明/占位 `img`、2 个 `svg`，没有常驻 DOM `video`。
- 页面主内容由 WebGL 渲染；项目媒体以 KTX2 压缩纹理加载，部分项目滚动到附近后按需请求 MP4。
- 3D 资源使用 GLB/Draco；纹理使用 KTX2/Basis；字体还提供 WebGL MSDF 字形数据。
- 音频包含 UI 动作、章节转场和循环环境声。
- 页面加载完成后文档高度仍等于视口高度，说明素材运动由虚拟滚动舞台统一驱动。

## 2. 参考站已确认的素材类型

| 类型 | 网络证据示例 | 在页面中的角色 | 复刻策略 |
| --- | --- | --- | --- |
| 主浮雕 GLB | `webgl/home/reliefs_high_compressed.glb` | 贯穿首页的石膏花鸟浮雕 | 独立制作未来遗迹 GLB |
| 背景模型 | `webgl/about/model/bg_low_draco.glb` | 深层背景与章节空间 | 低面数城市/空间站背景 |
| 项目装饰 GLB | `webgl/projects/fish.glb` | 项目段之间的动态生物元素 | 仿生无人机或机械水母 |
| 页脚 GLB | `webgl/footer/footer_compressed.glb` | 页脚收尾场景 | 未来空间站剖面 |
| 项目纹理 | `small_LV_01_v2_*.ktx2`、`small_David_Whyte_01_*.ktx2` 等 | WebGL 媒体平面 | 自制 WebP/AVIF，最终再转 KTX2 |
| 项目视频 | `LV_02_v2_*.mp4`、`Cartier_EOY_02_v2_*.mp4` | 进入可视区后动态播放 | 4 个短循环 MP4/WebM |
| LUT | `webgl/about/day.3DL`、`night.3DL`、`webgl/footer/lut.3dl` | 章节调色 | 自制冷灰/冰蓝 LUT，可选 |
| 环境音 | `Marble_Crack_10secLoop_no_filter.mp3` | 持续空间氛围 | 低频机械舱环境循环 |
| 事件音 | `actions.mp3`、`...Thunder_1.mp3` | 点击与页面转场 | 柔和电磁脉冲/舱门提示音 |
| WebGL 字体 | `webgl/msdf/...json` | Canvas 内文字 | 首版保持文字为 DOM，不制作 MSDF |
| 菜单动效 | `lotties/menu/home/*.json` | 菜单图标状态 | 用 SVG + GSAP 实现，避免额外 Lottie |

## 3. 未来世界素材清单

### A. 必需素材

| ID | 文件建议 | 规格 | 内容 | 使用位置 |
| --- | --- | --- | --- | --- |
| A01 | `textures/concrete-cool.webp` | 2048²，可平铺，< 450KB | 冷灰纸张/矿物纤维纹理 | 全局背景 |
| A02 | `models/orbital-ring.glb` | GLB 原型，< 1.5MB | 白色轨道环与小型舱体 | 首屏 |
| A03 | `models/bio-drone.glb` | GLB 原型，< 1.2MB | 仿生翼状无人机 | 宣言段 |
| A04 | `models/data-flora.glb` | GLB 原型，< 1.5MB | 白色机械植物与电路叶片 | 方法段 |
| A05 | `models/earth-arc.glb` | < 1.8MB，Draco | 低对比地球弧面 | 使命段 |
| A06 | `models/station-cutaway.glb` | < 2MB，Draco | 空间站剖面 | 页脚 |
| A07–A10 | `posters/project-0N.webp` | 1920 × 1080，< 500KB | 四个项目静态首帧 | 项目媒体与降级 |
| A11–A14 | `video/project-0N.mp4` | 1920 × 1080，6–10s，< 4MB | 无缝循环项目片段 | 项目媒体 |
| A15 | `audio/ambient-space.mp3` | 20–30s loop，< 1MB | 低频空间舱氛围 | 全局环境声 |
| A16 | `audio/ui-pulse.mp3` | < 1s，< 80KB | 声音开关/链接提示 | UI 反馈 |
| A17 | `audio/chapter-transition.mp3` | 2–3s，< 180KB | 章节跨越提示 | 关键章节 |
| A18 | `logo/mark.svg` | 单色矢量 | 独立未来世界字标/符号 | 固定导航 |

### B. 可选增强素材

| ID | 文件建议 | 价值 | 是否首轮需要 |
| --- | --- | --- | --- |
| B01 | `textures/noise-64.png` | shader 抖动与去色带 | 是，体积极小 |
| B02 | `textures/lut-ice.3dl` | 冰蓝统一调色 | 否，可先用材质色完成 |
| B03 | `models/micro-particles.glb` | 远景漂浮碎片 | 否，首轮可程序化点精灵 |
| B04 | KTX2 项目纹理 | 降低 GPU 上传与显存 | 第二轮性能优化 |
| B05 | WebM 视频副本 | 改善部分浏览器压缩率 | 发布前按兼容性决定 |

## 4. 四个项目媒体方向

所有媒体都应是 16:9、构图中央偏空、边缘有可裁切余量，以同时适配桌面浮动平面和移动全宽布局。

### 4.1 Orbital Habitat

- 外太空高亮环境中的白色环形居住站。
- 摄像机缓慢前移，地球弧面在远景滑过。
- 配色：冷灰、冰蓝，只有小面积橙色信号灯。

### 4.2 Synthetic Forest

- 生物科技温室，半透明叶片与机械根系共存。
- 慢速风动和光线扫描，避免快速粒子爆发。
- 配色：雾白、浅青、极淡绿色。

### 4.3 Lunar Archive

- 月面洞穴中的档案馆入口，几何建筑嵌入岩壁。
- 摄像机平行移动，尘埃缓慢漂浮。
- 配色：灰白、石墨黑、小面积红色导航标记。

### 4.4 Ocean Colony

- 深海透明穹顶城市，远处有机械水母经过。
- 水体折射保持缓慢，避免高频波纹影响文字可读性。
- 配色：蓝灰、银白、微弱青色发光。

## 5. 素材制作方式

### 5.1 3D

- Blender 制作或整理模型；几何以大块轮廓和浅浮雕细节为主。
- 统一米制尺度、Y-up 导出、中心点合理；动画烘焙到 GLB。
- 使用 Draco 压缩；首轮不要依赖运行时布尔或高成本置换。
- 材质以 `MeshStandardMaterial` 可表达的属性为主，避免不可移植节点。
- 每个模型提供桌面与移动两个 LOD；移动面数约为桌面的 35%–50%。

### 5.2 图片与视频

- 可用自制 3D 渲染或经过授权的生成式图像/视频；统一相机、光照和材质语言。
- 图片保留 1920 × 1080 母版，交付 WebP/AVIF；移动端可另出 960 × 1200 竖向裁切。
- 视频 H.264 MP4 为基线，24/30fps，无音轨，`faststart`，关键帧间隔不超过 2 秒。
- 每条视频同时提供 poster，poster 必须与首帧视觉一致。

### 5.3 音频

- 只使用自制或明确可商用音频。
- 环境声必须能无缝循环，不包含突然峰值。
- 导出 MP3/AAC，并在页面中通过 Web Audio API 做 gain ramp。

## 6. 生成式素材提示词骨架

提示词只定义统一方向，具体生成将在“准备替代素材”阶段执行。

```text
high-key museum-white future world, monumental orbital architecture,
matte ceramic and pale mineral surfaces, subtle relief detail,
soft overcast global illumination, restrained ice-blue accents,
editorial composition with generous negative space,
no cyberpunk neon, no UI overlay, no text, no logo,
cinematic but minimal, 16:9
```

每个项目只替换主体、环境和镜头运动，不改变整体材质、曝光与负空间要求。

## 7. 目录约定

```text
public/
  assets/
    audio/
    logo/
    models/
    posters/
    textures/
    video/
src/
  components/
  scenes/
  styles/
```

文件名使用小写 kebab-case，不保留来源站品牌名。模型和视频旁可放同名 `.license.txt`，记录作者、来源、授权范围和修改说明。

## 8. 加载与预算

- 首屏关键路径：背景纹理 + 字标 + 轨道环低模，合计目标 < 2.5MB。
- 初始总下载目标 < 5MB；其余项目在距离视口 1–1.5 个章节时预取。
- 单个 GLB < 2MB，单张 WebP < 500KB，单条视频 < 4MB。
- 同时解码视频不超过 1 条；同时驻留的 4K 纹理为 0。
- 首屏可交互目标：桌面中端设备 3s 内；移动网络慢时先显示 DOM 和 poster。

## 9. 法务与来源记录

- 不下载、复制或重新分发参考站的 GLB、KTX2、MP4、音频、字体或品牌标志。
- 截图仅作为内部视觉分析证据，不作为成品页面素材。
- 所有替代素材在引入仓库前必须记录授权；生成式素材记录模型、日期、提示词和后期处理。
- 最终验收时检查产物中不存在 `immersive-g.com`、客户品牌名或原站 CDN 地址。

## 10. 当前准备状态（2026-09-20）

已准备并落盘：

- 首屏视觉母版：`public/assets/hero/orbital-gateway-master.png`
- 四个项目 PNG 母版：`public/assets/posters/project-01-*.png` 至 `project-04-*.png`
- 冷灰材质纹理母版：`public/assets/textures/concrete-cool-master.png`
- 可直接用于网页的 WebP：`public/assets/hero/*.webp`、`public/assets/posters/*.webp`、`public/assets/textures/*.webp`
- 确定性噪声纹理：`public/assets/textures/noise-64.png`
- 原创轨道符号：`public/assets/logo/mark.svg`
- 完整生成提示词：`public/assets/generation-prompts.md`
- WebP 与噪声纹理处理脚本：`scripts/prepare_assets.py`
- Blender MCP 生成的 GLB 原型：`public/assets/models/orbital-ring.glb`、`bio-drone.glb`、`data-flora.glb`
- GLB 面数、尺寸与验证记录：`public/assets/models/README.md`

当前 WebP 均为 1672 × 941 的近似 16:9 画面，项目首帧分别为 135–242KB；背景纹理为 1254 × 1254、约 159KB，均低于本文件定义的预算。

GLB 当前完成 A02 轨道环、A03 仿生无人机和 A04 数据植物三个静态原型；A05 地球弧面、A06 空间站剖面、循环视频和音频尚未制作。这些未完成素材不会以静态图片冒充完成。

当前三个 GLB 依靠低面数控制体积，未启用 Draco；`scripts/inspect_glb.py` 检测到的扩展仅为 `KHR_materials_emissive_strength`。若后续首屏总预算需要进一步压缩，再在构建链路中增加 Draco/KTX2，而不把“文件小”误写为“已压缩”。

## 11. 连续背景升级素材（2026-09-21）

为解决章节之间背景过于空白、每幕彼此割裂的问题，新增 `public/assets/backdrops/` 作为固定世界背景的预渲染降级层：

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `relief-orbital-ring.webp` | `orbital-ring-hunyuan-v1-web.glb` 的 Blender 透明白模渲染 | Gateway 到 Manifesto 的大型轨道结构 |
| `relief-bio-drone.webp` | `bio-drone-hunyuan-v1-web.glb` 的 Blender 透明白模渲染 | Manifesto 飞行轨迹与章节连接 |
| `relief-data-flora.webp` | `data-flora-hunyuan-v1-web.glb` 的 Blender 透明白模渲染 | Protocol 到 Synthetic Forest 的机械植物浮雕 |
| `lunar-ocean-transition.webp` | OpenAI 图像生成后压缩 | Lunar Archive 到 Ocean Colony 的连续月面、等高线与水纹底图 |

三张浮雕母版均为 1800 × 1350 RGBA PNG，保留真实透明通道；网页使用 WebP 副本。月面—海流母版保留 1672 × 941 PNG，中央区域刻意保持低对比，避免干扰正文。简单的轨道线、风线、叶脉和声呐圈不烘进位图，后续由 SVG 与 GSAP 统一驱动，以便响应式裁切和反向滚动。
