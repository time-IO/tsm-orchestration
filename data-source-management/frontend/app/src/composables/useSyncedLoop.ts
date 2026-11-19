import { onBeforeUnmount, onMounted, readonly, ref } from 'vue';

/** Duration of one animation cycle shared by all synced animations. */
export const LOOP_DURATION_MS = 4000;

const phase = ref(0);
const reducedMotion = ref(false);
let subscribers = 0;
let frame: number | null = null;
let motionQuery: MediaQueryList | null = null;

function tick(now: number) {
  // Derive the phase from the global clock, not from the mount time, so
  // components mounted later (e.g. after expanding a card) stay in sync.
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

/**
 * Shared animation clock. Every subscriber reads the same phase in [0, 1),
 * driven by a single requestAnimationFrame loop, so all animations have the
 * same duration and run in lockstep. Respects `prefers-reduced-motion`.
 */
export function useSyncedLoop() {
  onMounted(() => {
    if (subscribers++ === 0) {
      if (motionQuery === null && typeof window.matchMedia === 'function') {
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
