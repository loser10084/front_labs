const video = document.querySelector('#story-video');
const scenes = [...document.querySelectorAll('.scene')];
const chapterCurrent = document.querySelector('#chapter-current');
const motionControl = document.querySelector('#motion-control');
const captureFrame = document.querySelector('#capture-frame');
const captureMode = new URLSearchParams(location.search).has('capture');
const captureFrames = [
  '../../assets/venus-poster.png',
  '../../assets/venus-face.png',
  '../../assets/venus-seam.png',
  '../../assets/venus-drapery.png',
  '../../assets/venus-poster.png',
];
let seekingEnabled = true;
let scheduled = false;

if (captureMode) document.documentElement.classList.add('capture-mode');

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const ease = (value) => value * value * (3 - 2 * value);

async function prepareVideo() {
  const source = video.dataset.src;
  try {
    const response = await fetch(source);
    if (!response.ok) throw new Error(`Video request failed: ${response.status}`);
    const blob = await response.blob();
    video.src = URL.createObjectURL(blob);
  } catch (error) {
    console.warn('Blob-backed video loading failed; using the original URL.', error);
    video.src = source;
  }
  video.load();
}

function updateStory() {
  scheduled = false;
  const maxScroll = document.documentElement.scrollHeight - innerHeight;
  const progress = maxScroll > 0 ? clamp(scrollY / maxScroll, 0, 1) : 0;
  document.documentElement.style.setProperty('--scroll-progress', progress.toFixed(4));

  if (seekingEnabled && Number.isFinite(video.duration) && video.duration > 0) {
    const targetTime = ease(progress) * Math.max(0, video.duration - 0.04);
    if (Math.abs(video.currentTime - targetTime) > 0.035) video.currentTime = targetTime;
  }

  const viewportCenter = scrollY + innerHeight * 0.5;
  let activeIndex = 0;
  scenes.forEach((scene, index) => {
    const start = scene.offsetTop;
    const end = start + scene.offsetHeight;
    if (viewportCenter >= start && viewportCenter < end) activeIndex = index;
    scene.classList.toggle('is-active', index === activeIndex);
  });
  if (captureMode && captureFrame.dataset.scene !== String(activeIndex)) {
    captureFrame.dataset.scene = String(activeIndex);
    captureFrame.src = captureFrames[activeIndex];
  }
  chapterCurrent.textContent = String(activeIndex + 1).padStart(2, '0');
}

function requestUpdate() {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(updateStory);
}

video.addEventListener('loadedmetadata', () => {
  video.pause();
  updateStory();
});
window.addEventListener('scroll', requestUpdate, { passive: true });
window.addEventListener('resize', requestUpdate);
motionControl.addEventListener('click', () => {
  seekingEnabled = !seekingEnabled;
  motionControl.setAttribute('aria-label', seekingEnabled ? '暂停滚动影片' : '继续滚动影片');
  motionControl.style.opacity = seekingEnabled ? '1' : '.48';
  if (seekingEnabled) updateStory();
});
updateStory();
prepareVideo();
