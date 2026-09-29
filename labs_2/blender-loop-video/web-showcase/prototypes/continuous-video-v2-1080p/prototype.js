const canvas = document.querySelector('#story-canvas');
const context = canvas.getContext('2d', { alpha: false });
const scenes = [...document.querySelectorAll('.scene')];
const chapterCurrent = document.querySelector('#chapter-current');
const motionControl = document.querySelector('#motion-control');
const scrollModeControl = document.querySelector('#scroll-mode');
const scrollModeValue = document.querySelector('#scroll-mode-value');
const captureFrame = document.querySelector('#capture-frame');
const urlParams = new URLSearchParams(location.search);
const captureMode = urlParams.has('capture');
const captureFrames = [
  './assets/frame-001.png', './assets/frame-076.png', './assets/frame-151.png',
  './assets/frame-226.png', './assets/frame-300.png',
];

const FRAME_COUNT = 300;
const CACHE_LIMIT = 42;
const DIRECT_WHEEL_LIMIT = 90;
const frameBlobs = new Map();
const frameBitmaps = new Map();
const inflightFrames = new Map();
const inflightBlobs = new Map();
let seekingEnabled = true;
let updateScheduled = false;
let renderScheduled = false;
let drawing = false;
let targetFrame = 0;
let presentedFrame = 0;
let directScrollY = scrollY;

class WheelIntentFilter {
  constructor() {
    this.reset();
  }

  reset() {
    this.direction = 0;
    this.samples = [];
    this.lastTime = 0;
  }

  accepts(delta, time = performance.now()) {
    const direction = Math.sign(delta);
    const magnitude = Math.abs(delta);
    if (!direction || !Number.isFinite(magnitude)) return false;

    const gap = time - this.lastTime;
    const previousMagnitude = this.samples.at(-1) ?? 0;
    const startsNewGesture = direction !== this.direction
      || gap > 140
      || (magnitude > 24 && magnitude > previousMagnitude * 1.8);

    if (startsNewGesture) {
      this.direction = direction;
      this.samples = [];
    }

    this.lastTime = time;
    this.samples.push(magnitude);
    if (this.samples.length > 6) this.samples.shift();
    if (this.samples.length < 2) return true;

    const recent = this.samples.slice(-2);
    const monotonicallyDecaying = recent.every(
      (value, index) => index === 0 || value <= recent[index - 1] * 1.08,
    );
    const hasFaded = recent[1] < recent[0] * 0.96;
    return !(monotonicallyDecaying && hasFaded);
  }
}

const wheelIntent = new WheelIntentFilter();

const telemetry = {
  ready: false, preloaded: false, drawCount: 0, maxConcurrentDraws: 0, concurrentDraws: 0,
  targetFrame: 0, presentedFrame: 0, scrollMode: 'native', directWheelEnabled: false,
  acceptedWheelEvents: 0, rejectedWheelEvents: 0, lastWheelAccepted: false,
  wheelEvents: 0, scrollEvents: 0, lastWheelDeltaY: 0, lastWheelDeltaMode: 0,
  lastWheelAt: 0, lastScrollAt: 0,
};
window.__scrollCanvas = telemetry;

if (captureMode) document.documentElement.classList.add('capture-mode');
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const frameUrl = index => `./assets/scroll-frames/frame-${String(index + 1).padStart(3, '0')}.webp`;

async function loadFrameBlob(index) {
  if (frameBlobs.has(index)) return frameBlobs.get(index);
  if (inflightBlobs.has(index)) return inflightBlobs.get(index);
  const task = (async () => {
    const response = await fetch(frameUrl(index));
    if (!response.ok) throw new Error(`Frame ${index + 1} failed: ${response.status}`);
    const blob = await response.blob();
    frameBlobs.set(index, blob);
    return blob;
  })().finally(() => inflightBlobs.delete(index));
  inflightBlobs.set(index, task);
  return task;
}

async function loadFrame(index) {
  if (frameBitmaps.has(index)) return frameBitmaps.get(index);
  if (inflightFrames.has(index)) return inflightFrames.get(index);
  const task = (async () => {
    const blob = await loadFrameBlob(index);
    const bitmap = await createImageBitmap(blob);
    frameBitmaps.set(index, bitmap);
    return bitmap;
  })().finally(() => inflightFrames.delete(index));
  inflightFrames.set(index, task);
  return task;
}

async function preloadFrameBlobs() {
  let cursor = 0;
  const worker = async () => {
    while (cursor < FRAME_COUNT) {
      const index = cursor;
      cursor += 1;
      await loadFrameBlob(index);
    }
  };
  await Promise.all(Array.from({ length: 12 }, worker));
  telemetry.preloaded = true;
}

function trimBitmapCache(center) {
  if (frameBitmaps.size <= CACHE_LIMIT) return;
  const removable = [...frameBitmaps.keys()]
    .filter(index => index !== presentedFrame)
    .sort((a, b) => Math.abs(b - center) - Math.abs(a - center));
  while (frameBitmaps.size > CACHE_LIMIT && removable.length) {
    const index = removable.shift();
    frameBitmaps.get(index)?.close();
    frameBitmaps.delete(index);
  }
}

function updateSceneState(progress) {
  document.documentElement.style.setProperty('--scroll-progress', progress.toFixed(4));
  const activeIndex = Math.min(
    scenes.length - 1,
    Math.floor(clamp(progress, 0, 0.999999) * scenes.length),
  );
  scenes.forEach((scene, index) => scene.classList.toggle('is-active', index === activeIndex));
  if (captureMode && captureFrame.dataset.scene !== String(activeIndex)) {
    captureFrame.dataset.scene = String(activeIndex);
    captureFrame.src = captureFrames[activeIndex];
  }
  chapterCurrent.textContent = String(activeIndex + 1).padStart(2, '0');
}

function drawBitmap(bitmap, index) {
  context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  presentedFrame = index;
  telemetry.presentedFrame = index;
  telemetry.drawCount += 1;
  if (!captureMode) updateSceneState(index / (FRAME_COUNT - 1));
  trimBitmapCache(index);
}

async function renderNextFrame() {
  renderScheduled = false;
  if (drawing || !seekingEnabled || presentedFrame === targetFrame) return;
  const nextFrame = targetFrame;
  const requestedDirection = Math.sign(nextFrame - presentedFrame);

  drawing = true;
  telemetry.concurrentDraws += 1;
  telemetry.maxConcurrentDraws = Math.max(telemetry.maxConcurrentDraws, telemetry.concurrentDraws);
  try {
    const bitmap = await loadFrame(nextFrame);
    const liveDirection = Math.sign(targetFrame - presentedFrame);
    if (liveDirection === 0 || liveDirection === requestedDirection) {
      drawBitmap(bitmap, nextFrame);
    }
  } catch (error) {
    console.error('Canvas frame rendering failed.', error);
    document.documentElement.classList.add('frame-error');
  } finally {
    telemetry.concurrentDraws -= 1;
    drawing = false;
  }
  if (presentedFrame !== targetFrame) requestRender();
}

function requestRender() {
  if (renderScheduled || drawing) return;
  renderScheduled = true;
  requestAnimationFrame(renderNextFrame);
}

function updateStory() {
  updateScheduled = false;
  const maxScroll = document.documentElement.scrollHeight - innerHeight;
  const progress = maxScroll > 0 ? clamp(scrollY / maxScroll, 0, 1) : 0;
  targetFrame = Math.round(progress * (FRAME_COUNT - 1));
  telemetry.targetFrame = targetFrame;
  if (captureMode) updateSceneState(progress);
  if (seekingEnabled) requestRender();
}

function requestUpdate() {
  if (updateScheduled) return;
  updateScheduled = true;
  requestAnimationFrame(updateStory);
}

function setScrollMode(mode) {
  const wantsDirect = mode === 'direct';
  directScrollY = scrollY;
  wheelIntent.reset();
  telemetry.scrollMode = wantsDirect ? 'direct' : 'native';
  telemetry.directWheelEnabled = wantsDirect;
  scrollModeValue.textContent = wantsDirect ? '直控' : '原生';
  document.documentElement.dataset.scrollMode = telemetry.scrollMode;
  scrollModeControl.setAttribute('aria-pressed', String(wantsDirect));
}

function wheelDeltaPixels(event) {
  if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) return event.deltaY * 16;
  if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) return event.deltaY * innerHeight;
  return event.deltaY;
}

async function initializeFrames() {
  try {
    drawBitmap(await loadFrame(0), 0);
    await preloadFrameBlobs();
    telemetry.ready = true;
    updateStory();
  } catch (error) {
    console.error('Canvas frame sequence failed to initialize.', error);
    document.documentElement.classList.add('frame-error');
  }
}

window.addEventListener('wheel', event => {
  const now = performance.now();
  telemetry.wheelEvents += 1;
  telemetry.lastWheelDeltaY = event.deltaY;
  telemetry.lastWheelDeltaMode = event.deltaMode;
  telemetry.lastWheelAt = now;

  if (telemetry.scrollMode !== 'direct' || event.ctrlKey) return;
  if (Math.abs(event.deltaX) > Math.abs(event.deltaY)) return;

  const delta = wheelDeltaPixels(event);
  if (!delta) return;
  event.preventDefault();

  const accepted = wheelIntent.accepts(delta, now);
  telemetry.lastWheelAccepted = accepted;
  if (!accepted) {
    telemetry.rejectedWheelEvents += 1;
    return;
  }

  telemetry.acceptedWheelEvents += 1;
  const maxScroll = document.documentElement.scrollHeight - innerHeight;
  const step = clamp(delta, -DIRECT_WHEEL_LIMIT, DIRECT_WHEEL_LIMIT);
  directScrollY = clamp(directScrollY + step, 0, maxScroll);
  window.scrollTo(0, directScrollY);
  requestUpdate();
}, { passive: false, capture: true });
window.addEventListener('scroll', () => {
  directScrollY = scrollY;
  telemetry.scrollEvents += 1;
  telemetry.lastScrollAt = performance.now();
  requestUpdate();
}, { passive: true });
window.addEventListener('resize', () => {
  directScrollY = clamp(scrollY, 0, document.documentElement.scrollHeight - innerHeight);
  requestUpdate();
});
scrollModeControl.addEventListener('click', () => {
  setScrollMode(telemetry.scrollMode === 'direct' ? 'native' : 'direct');
});
motionControl.addEventListener('click', () => {
  seekingEnabled = !seekingEnabled;
  motionControl.setAttribute('aria-label', seekingEnabled ? '暂停滚动影片' : '继续滚动影片');
  motionControl.style.opacity = seekingEnabled ? '1' : '.48';
  if (seekingEnabled) {
    updateStory();
    requestRender();
  }
});

setScrollMode(urlParams.get('scroll') === 'native' ? 'native' : 'direct');
updateStory();
initializeFrames();
