import { copyToClipboard } from 'quasar';
import {
  onScopeDispose,
  ref,
  toValue,
  watch,
  type ComponentPublicInstance,
  type MaybeRefOrGetter,
} from 'vue';

type CopyTarget = HTMLElement | ComponentPublicInstance | null | undefined;
type CopyState = 'idle' | 'copied' | 'failed';

const LABELS: Record<CopyState, string> = {
  idle: 'Click to copy',
  copied: 'Copied',
  failed: 'Failed to copy',
};

const TOOLTIP_OFFSET_PX = 6;
// must match the transition duration of .copy-tooltip in app.scss
const TRANSITION_MS = 300;

function resolveElement(target: CopyTarget): HTMLElement | null {
  if (!target) return null;
  if (target instanceof HTMLElement) return target;
  return target.$el instanceof HTMLElement ? target.$el : null;
}

/**
 * Turns `target` into a click-to-copy element: hovering shows a tooltip
 * above it ("Click to copy"), clicking copies `text` and switches the
 * tooltip to a green "Copied".
 */
export function useCopy(target: MaybeRefOrGetter<CopyTarget>, text: MaybeRefOrGetter<string>) {
  const state = ref<CopyState>('idle');
  let tooltip: HTMLDivElement | null = null;
  let removeTimer: ReturnType<typeof setTimeout> | undefined;

  function update() {
    if (!tooltip) return;
    tooltip.textContent = LABELS[state.value];
    tooltip.classList.toggle('copy-tooltip--copied', state.value === 'copied');
    tooltip.classList.toggle('copy-tooltip--failed', state.value === 'failed');
  }

  function show(el: HTMLElement) {
    clearTimeout(removeTimer);
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.setAttribute('role', 'tooltip');
      tooltip.className = 'copy-tooltip q-tooltip--style';
      document.body.appendChild(tooltip);
    }
    state.value = 'idle';
    update();

    const rect = el.getBoundingClientRect();
    tooltip.style.left = `${rect.left + rect.width / 2}px`;
    tooltip.style.top = `${rect.top - TOOLTIP_OFFSET_PX}px`;

    // force a reflow so the enter transition starts from the hidden state
    void tooltip.offsetWidth;
    tooltip.classList.add('copy-tooltip--visible');
  }

  function hide() {
    if (!tooltip) return;
    const leaving = tooltip;
    leaving.classList.remove('copy-tooltip--visible');
    clearTimeout(removeTimer);
    removeTimer = setTimeout(() => {
      leaving.remove();
      if (tooltip === leaving) tooltip = null;
    }, TRANSITION_MS);
  }

  function destroy() {
    clearTimeout(removeTimer);
    tooltip?.remove();
    tooltip = null;
  }

  async function copy() {
    try {
      await copyToClipboard(toValue(text));
      state.value = 'copied';
    } catch {
      state.value = 'failed';
    }
    update();
  }

  function onEnter(event: Event) {
    show(event.currentTarget as HTMLElement);
  }

  function onClick(event: Event) {
    event.stopPropagation();
    void copy();
  }

  watch(
    () => resolveElement(toValue(target)),
    (el, _prev, onCleanup) => {
      if (!el) return;
      el.addEventListener('mouseenter', onEnter);
      el.addEventListener('mouseleave', hide);
      el.addEventListener('click', onClick);
      onCleanup(() => {
        el.removeEventListener('mouseenter', onEnter);
        el.removeEventListener('mouseleave', hide);
        el.removeEventListener('click', onClick);
        destroy();
      });
    },
    { immediate: true, flush: 'post' },
  );

  onScopeDispose(destroy);

  return { copy, state };
}
