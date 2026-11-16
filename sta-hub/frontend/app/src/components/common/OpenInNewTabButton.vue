<template>
  <q-btn
    flat
    :round="round"
    :dense="dense"
    :size="size"
    :color="color"
    icon="open_in_new"
    type="a"
    :href="disabled ? undefined : href"
    :class="{ 'open-in-new-tab-button--disabled': disabled }"
    :aria-disabled="disabled"
    :aria-label="tooltipText"
    target="_blank"
    rel="noopener noreferrer"
  >
    <q-tooltip>{{ tooltipText }}</q-tooltip>
  </q-btn>
</template>

<script setup lang="ts">
const {
  href,
  tooltipText = 'Open in new tab',
  disabled = false,
  size,
  color,
  dense = false,
  round = true,
} = defineProps<{
  href: string;
  tooltipText?: string | undefined;
  disabled?: boolean;
  size?: string;
  color?: string;
  dense?: boolean;
  round?: boolean;
}>();
</script>

<style scoped>
.open-in-new-tab-button--disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
