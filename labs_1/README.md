# 滚动驱动建筑镜头示例

根据参考录屏中电脑显示的建筑页面，制作固定视口、滚动驱动镜头推进和分段标题动画。录屏中真正的建筑漫游原片并未提供，当前实现用三层建筑画面和连续空间变换近似复刻运动关系。

## 运行

在本目录执行：

```powershell
python scripts/serve.py
```

然后打开 `http://127.0.0.1:5188/`，向下滚动。也可以直接双击 `index.html`。需要更换端口时可执行 `python scripts/serve.py 端口号`。

## 实现要点

1. `.scroll-story` 提供约四屏滚动距离，`.stage` 用 `position: sticky` 固定在视口。
2. `main.js` 将页面滚动距离归一化为 `0..1`，用单调阻尼跟随平滑输入，再映射到 Web Animations API 的暂停时间轴。
3. 三层画面使用同方向的 scale、translate 和短区间曝光交接完成连续摄影机推进；不使用动态模糊或硬边蒙版。标题按行错峰，编号同步滚动。
4. 整条时间轴可正向或反向 scrub。关键运动节点和录屏逐帧对比结果见 `MOTION_ANALYSIS.md`。

`assets/architecture-v2.mp4` 与 `scripts/build-demo-video.ps1` 保留作素材实验，当前页面的运动由三张图片和 Web Animations API 实时生成。

## 画面素材

- `assets/exterior-v2.png`：参考录屏中的雾中悬挑白色混凝土住宅，左侧留出标题空间。
- `assets/corridor-v2.png`：同一住宅的临水玻璃走廊、反光石材地面与右侧暖木墙。
- `assets/timber-v2.png`：同一住宅的木饰面核心空间、悬浮楼梯与右侧森林玻璃幕墙。

三张图均由内置 `imagegen` 根据录屏画面生成；提示词要求 16:9 写实建筑可视化、统一的白色混凝土与暖木材质，并排除录屏中的显示器、桌面、字幕和网页界面。旧版 Unsplash 照片保留在 `assets` 中供对比，当前页面未引用。

页面使用的 `*-hq.webp` 是原图经 Lanczos 放大与轻量锐化生成的 3344×1882 版本，用于在推进镜头中保持细节；原始 PNG 继续保留作为母版。

录屏中的布局和文字是视觉参考；此示例没有复制原网站源码或建筑漫游视频。
