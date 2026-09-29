const story = document.querySelector("#story");
const stage = document.querySelector("#stage");
const media = [...document.querySelectorAll("[data-media]")];
const copies = [...document.querySelectorAll("[data-copy]")];
const counterTrack = document.querySelector("#counter-track");
const progressFill = document.querySelector("#progress-fill");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

const DURATION = 1000;
const TRANSITION_ONE = 0.37;
const TRANSITION_TWO = 0.74;

let targetProgress = 0;
let renderedProgress = 0;
let lastFrame = performance.now();
let sceneIndex = 0;

const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));

function pausedAnimation(element, keyframes) {
  const animation = element.animate(keyframes, {
    duration: DURATION,
    fill: "both",
    easing: "linear",
  });
  animation.pause();
  return animation;
}

/*
 * All three shots share one forward camera direction. The overlaps are long
 * enough to read as moving through the space instead of switching images.
 * The overlap is deliberately short to avoid a double-exposure look. The
 * 3344 × 1882 derivatives retain detail during the deeper push-in.
 */
const mediaAnimations = [
  pausedAnimation(media[0], [
    { offset: 0, opacity: 1, transform: "translate3d(0, 0, 0) scale(1)", easing: "cubic-bezier(.22,.61,.36,1)" },
    { offset: 0.2, opacity: 1, transform: "translate3d(-0.3%, 0, 0) scale(1.025)", easing: "cubic-bezier(.4,0,.35,1)" },
    { offset: 0.28, opacity: 1, transform: "translate3d(-1%, 0.15%, 0) scale(1.075)", easing: "cubic-bezier(.42,0,.58,1)" },
    { offset: 0.34, opacity: 1, transform: "translate3d(-3%, 0.4%, 0) scale(1.24)", easing: "cubic-bezier(.5,.05,.7,.45)" },
    { offset: 0.368, opacity: 1, transform: "translate3d(-6.5%, 0.8%, 0) scale(1.58)", easing: "cubic-bezier(.4,0,.3,1)" },
    { offset: 0.392, opacity: 0, transform: "translate3d(-9%, 1%, 0) scale(1.78)" },
    { offset: 1, opacity: 0, transform: "translate3d(-9%, 1%, 0) scale(1.78)" },
  ]),
  pausedAnimation(media[1], [
    { offset: 0, opacity: 0, transform: "translate3d(1.5%, 0.15%, 0) scale(1.15)" },
    { offset: 0.356, opacity: 0, transform: "translate3d(1.5%, 0.15%, 0) scale(1.15)", easing: "cubic-bezier(.2,.65,.3,1)" },
    { offset: 0.374, opacity: 0.72, transform: "translate3d(.7%, 0.08%, 0) scale(1.1)", easing: "cubic-bezier(.22,.61,.36,1)" },
    { offset: 0.4, opacity: 1, transform: "translate3d(0, 0, 0) scale(1.045)", easing: "cubic-bezier(.22,.61,.36,1)" },
    { offset: 0.43, opacity: 1, transform: "translate3d(0, 0, 0) scale(1)", easing: "cubic-bezier(.22,.61,.36,1)" },
    { offset: 0.58, opacity: 1, transform: "translate3d(-0.35%, 0, 0) scale(1.025)", easing: "cubic-bezier(.4,0,.35,1)" },
    { offset: 0.66, opacity: 1, transform: "translate3d(-1%, 0, 0) scale(1.07)", easing: "cubic-bezier(.42,0,.58,1)" },
    { offset: 0.72, opacity: 1, transform: "translate3d(-3%, 0, 0) scale(1.24)", easing: "cubic-bezier(.5,.05,.7,.45)" },
    { offset: 0.748, opacity: 1, transform: "translate3d(-6%, 0, 0) scale(1.55)", easing: "cubic-bezier(.4,0,.3,1)" },
    { offset: 0.772, opacity: 0, transform: "translate3d(-8.5%, 0, 0) scale(1.75)" },
    { offset: 1, opacity: 0, transform: "translate3d(-8.5%, 0, 0) scale(1.75)" },
  ]),
  pausedAnimation(media[2], [
    { offset: 0, opacity: 0, transform: "translate3d(1.5%, 0, 0) scale(1.14)" },
    { offset: 0.736, opacity: 0, transform: "translate3d(1.5%, 0, 0) scale(1.14)", easing: "cubic-bezier(.2,.65,.3,1)" },
    { offset: 0.754, opacity: 0.72, transform: "translate3d(.7%, 0, 0) scale(1.095)", easing: "cubic-bezier(.22,.61,.36,1)" },
    { offset: 0.78, opacity: 1, transform: "translate3d(0, 0, 0) scale(1.04)", easing: "cubic-bezier(.22,.61,.36,1)" },
    { offset: 0.81, opacity: 1, transform: "translate3d(0, 0, 0) scale(1)", easing: "cubic-bezier(.22,.61,.36,1)" },
    { offset: 1, opacity: 1, transform: "translate3d(-0.8%, 0, 0) scale(1.04)" },
  ]),
];

const copyWindows = [
  { enter: 0, settle: 0, hold: 0.27, exit: 0.355 },
  { enter: 0.395, settle: 0.44, hold: 0.65, exit: 0.735 },
  { enter: 0.775, settle: 0.82, hold: 1, exit: 1 },
];

const copyAnimations = copies.map((copy, copyIndex) => {
  const window = copyWindows[copyIndex];
  return [...copy.querySelectorAll(".copy-line")].map((line, lineIndex) => {
    const enterStagger = copyIndex === 0 ? 0 : lineIndex * 0.01;
    const exitStagger = lineIndex * 0.004;
    const enter = Math.min(1, window.enter + enterStagger);
    const settle = Math.min(1, window.settle + enterStagger);
    const hold = Math.max(settle, window.hold + exitStagger);
    const exit = Math.max(hold, window.exit + exitStagger);
    const keyframes = [];

    if (enter > 0) {
      keyframes.push({ offset: 0, opacity: 0, transform: "translate3d(18px, 0, 0) scale(.995)" });
      keyframes.push({
        offset: enter,
        opacity: 0,
        transform: "translate3d(18px, 0, 0) scale(.995)",
        easing: "cubic-bezier(.22,.61,.36,1)",
      });
    }
    keyframes.push({ offset: settle, opacity: 1, transform: "translate3d(0, 0, 0) scale(1)" });
    keyframes.push({
      offset: hold,
      opacity: 1,
      transform: "translate3d(0, 0, 0) scale(1)",
      easing: "cubic-bezier(.4,0,.3,1)",
    });
    if (exit < 1) {
      keyframes.push({ offset: exit, opacity: 0, transform: "translate3d(-22px, 0, 0) scale(1.005)" });
      keyframes.push({ offset: 1, opacity: 0, transform: "translate3d(-22px, 0, 0) scale(1.005)" });
    }
    return pausedAnimation(line, keyframes);
  });
});

const counterAnimation = pausedAnimation(counterTrack, [
  { offset: 0, transform: "translateY(0)" },
  { offset: 0.35, transform: "translateY(0)", easing: "cubic-bezier(.22,.61,.36,1)" },
  { offset: 0.41, transform: "translateY(-1.4em)" },
  { offset: 0.73, transform: "translateY(-1.4em)", easing: "cubic-bezier(.22,.61,.36,1)" },
  { offset: 0.79, transform: "translateY(-2.8em)" },
  { offset: 1, transform: "translateY(-2.8em)" },
]);

function updateTarget() {
  const travel = Math.max(1, story.offsetHeight - window.innerHeight);
  targetProgress = clamp(-story.getBoundingClientRect().top / travel);
}

function updateScene(progress) {
  const nextScene = progress < TRANSITION_ONE ? 0 : progress < TRANSITION_TWO ? 1 : 2;
  if (nextScene === sceneIndex) return;
  sceneIndex = nextScene;
  stage.dataset.scene = String(sceneIndex);
  copies.forEach((copy, index) => {
    const active = index === sceneIndex;
    copy.classList.toggle("is-active", active);
    copy.setAttribute("aria-hidden", String(!active));
  });
}

function renderTimeline(progress) {
  const time = clamp(progress) * DURATION;
  mediaAnimations.forEach((animation) => { animation.currentTime = time; });
  copyAnimations.flat().forEach((animation) => { animation.currentTime = time; });
  counterAnimation.currentTime = time;
  progressFill.style.transform = `scaleX(${clamp(progress)})`;
  updateScene(progress);
}

function tick(now) {
  const dt = Math.min(0.032, Math.max(0.001, (now - lastFrame) / 1000));
  lastFrame = now;

  if (reducedMotion.matches) {
    renderedProgress = targetProgress;
  } else {
    const smoothing = 1 - Math.exp(-10 * dt);
    renderedProgress += (targetProgress - renderedProgress) * smoothing;
    if (Math.abs(targetProgress - renderedProgress) < 0.00002) {
      renderedProgress = targetProgress;
    }
  }

  renderTimeline(renderedProgress);
  requestAnimationFrame(tick);
}

window.addEventListener("scroll", updateTarget, { passive: true });
window.addEventListener("resize", updateTarget);
reducedMotion.addEventListener("change", updateTarget);
updateTarget();
renderTimeline(renderedProgress);
requestAnimationFrame(tick);
