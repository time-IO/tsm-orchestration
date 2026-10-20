<template>
  <q-btn
    flat
    :round="round"
    :dense="dense"
    :size="size"
    :color="color"
    icon="open_in_new"
    type="a"
    :href="href"
    :class="{ 'open-in-new-tab-button--disabled': disabledHint }"
    :aria-disabled="!!disabledHint"
    :aria-label="tooltip"
    target="_blank"
    rel="noopener noreferrer"
    @click="onClick"
  >
    <q-tooltip>{{ disabledHint ?? tooltip }}</q-tooltip>
  </q-btn>
</template>

<script setup lang="ts">
const {
  href,
  tooltip = 'Open in new tab',
  disabledHint = null,
  size,
  color,
  dense = false,
  round = true,
} = defineProps<{
  href: string;
  tooltip?: string;
  // disables the button and is shown as its tooltip instead
  disabledHint?: string | null;
  size?: string;
  color?: string;
  dense?: boolean;
  round?: boolean;
}>();

function onClick(event: Event) {
  if (disabledHint) event.preventDefault();
}
</script>

<style scoped>
.open-in-new-tab-button--disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
