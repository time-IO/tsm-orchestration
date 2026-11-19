import { onBeforeUnmount, onMounted, readonly, ref } from 'vue';

export const LOOP_DURATION_MS = 4000; // duration of one animation cycle shared by all animations

const phase = ref(0);
const reducedMotion = ref(false);
let subscribers = 0;
let frame: number | null = null;
let motionQuery: MediaQueryList | null = null;

function tick(now: number) {
  phase.value = (now % LOOP_DURATION_MS) / LOOP_DURATION_MS;
  frame = requestAnimationFrame(tick);
}

function start() {
  if (frame === null && !reducedMotion.value) {
    frame = requestAnimationFrame(tick);
  }
}

function stop() {
  if (frame !== null) {
    cancelAnimationFrame(frame);
    frame = null;
  }
}

function onMotionChange(event: MediaQueryListEvent) {
  reducedMotion.value = event.matches;
  if (event.matches) {
    stop();
  } else if (subscribers > 0) {
    start();
  }
}

export function useSyncedLoop() {
  onMounted(() => {
    if (subscribers++ === 0) {
      if (motionQuery === null && typeof window.matchMedia === 'function') {
        // respect user preferences: https://developer.mozilla.org/de/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion
        motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        reducedMotion.value = motionQuery.matches;
        motionQuery.addEventListener('change', onMotionChange);
      }
      start();
    }
  });

  onBeforeUnmount(() => {
    if (--subscribers === 0) {
      stop();
    }
  });

  return { phase: readonly(phase), reducedMotion: readonly(reducedMotion) };
}
