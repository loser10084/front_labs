# VENUS RECONSTRUCTED 网页展示

独立的静态展览页，使用本实验的 10 秒循环视频及分镜剧照，不依赖构建工具或外部字体服务。

在此目录运行 `python -m http.server 5174`，然后打开 `http://127.0.0.1:5174/`。不要直接以 `file://` 打开，以免浏览器限制视频加载。

视频播放/暂停、进度线、细节切换与页内导航可操作；系统设置“减少动态效果”时视频默认暂停。当前接入的是 1080p、30 FPS、10 秒最终成片与同分辨率剧照。原 720p 预览素材仍保留在 `assets/`，未覆盖。

设计概念保存在 `concepts/`，最终 1080p 网页的真实浏览器首屏预览为 `previews/desktop-final-1080p.png` 与 `previews/mobile-final-1080p.png`。在本地服务器运行时，可执行 `python tests/smoke.py` 检查桌面/手机布局、视频、交互与减少动态效果设置（需安装 Python Playwright 及 Chromium）。
