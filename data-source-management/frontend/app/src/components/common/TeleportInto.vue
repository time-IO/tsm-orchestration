<template>
  <Teleport v-if="targetElement" :to="targetElement">
    <slot />
  </Teleport>
</template>

<script setup lang="ts">
/**
 * Teleports its slot content into an element inside another component (matched by `selector`
 * within the component's root element). Useful to add content to a part of a component that
 * offers no slot for it, without replacing that part's default content.
 *
 * The content is appended as the last child of the matched element (use CSS `order` to move it
 * within a flex container). The element is looked up once the target is mounted, so the matched
 * element must exist then and must not be re-created by the target component afterwards.
 *
 * Usage:
 *   <q-table ref="table" ... />
 *   <teleport-into :target="table" selector=".q-table__bottom"> ... </teleport-into>
 */
import { computed } from 'vue';

const { target, selector } = defineProps<{
  target: object | null;
  selector: string;
}>();

const targetElement = computed(() => {
  const root: unknown =
    target instanceof HTMLElement ? target : (target as { $el?: unknown } | null)?.$el;
  return root instanceof HTMLElement ? root.querySelector<HTMLElement>(selector) : null;
});
</script>
