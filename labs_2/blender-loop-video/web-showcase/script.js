const video = document.querySelector('#hero-video');
const playToggle = document.querySelector('#play-toggle');
const progressFill = document.querySelector('#film-progress-fill');
const timeLabel = document.querySelector('#film-time');
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

function syncPlaybackButton() {
  const paused = video.paused;
  playToggle.setAttribute('aria-pressed', String(paused));
  playToggle.setAttribute('aria-label', paused ? '播放背景视频' : '暂停背景视频');
}

function syncProgress() {
  if (!Number.isFinite(video.duration) || video.duration <= 0) return;
  progressFill.style.width = `${Math.min(100, (video.currentTime / video.duration) * 100)}%`;
  const seconds = Math.floor(video.currentTime).toString().padStart(2, '0');
  timeLabel.textContent = `00:${seconds} / LOOP`;
}

playToggle.addEventListener('click', async () => {
  if (video.paused) {
    try { await video.play(); } catch { syncPlaybackButton(); }
  } else {
    video.pause();
  }
  syncPlaybackButton();
});
video.addEventListener('play', syncPlaybackButton);
video.addEventListener('pause', syncPlaybackButton);
video.addEventListener('timeupdate', syncProgress);
video.addEventListener('loadedmetadata', syncProgress);
if (reduceMotion.matches) video.pause();
reduceMotion.addEventListener('change', (event) => {
  if (event.matches) video.pause();
  syncPlaybackButton();
});
syncPlaybackButton();

const details = [
  { src: './assets/venus-face-final-1080p.png', alt: '断臂维纳斯的面部与胸部近景', caption: '面部 / 古典轮廓' },
  { src: './assets/venus-seam-final-1080p.png', alt: '雕塑石材与黑色修复材质的接缝近景', caption: '修复 / 异质接缝' },
  { src: './assets/venus-drapery-final-1080p.png', alt: '雕塑衣袍和不同材质的局部近景', caption: '衣袍 / 材料层次' },
];
const detailImage = document.querySelector('#detail-image');
const detailCaption = document.querySelector('#detail-caption');
const detailNumber = document.querySelector('#detail-number');
const detailPanel = document.querySelector('#detail-panel');
const detailTabs = [...document.querySelectorAll('.detail-viewer__rail button')];
let detailChangeTimer;

function selectDetail(index) {
  const detail = details[index];
  if (!detail) return;
  clearTimeout(detailChangeTimer);
  detailImage.classList.add('is-changing');
  detailTabs.forEach((tab, tabIndex) => {
    const selected = tabIndex === index;
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  detailPanel.setAttribute('aria-labelledby', detailTabs[index].id);
  detailChangeTimer = window.setTimeout(() => {
    detailImage.src = detail.src;
    detailImage.alt = detail.alt;
    detailCaption.textContent = detail.caption;
    detailNumber.textContent = `0${index + 1} — 03`;
    if (detailImage.complete) detailImage.classList.remove('is-changing');
  }, 180);
}

detailImage.addEventListener('load', () => detailImage.classList.remove('is-changing'));
detailTabs.forEach((tab, index) => {
  tab.addEventListener('click', () => selectDetail(index));
  tab.addEventListener('keydown', (event) => {
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? detailTabs.length - 1 : (index + (['ArrowRight', 'ArrowDown'].includes(event.key) ? 1 : -1) + detailTabs.length) % detailTabs.length;
    selectDetail(next);
    detailTabs[next].focus();
  });
});
