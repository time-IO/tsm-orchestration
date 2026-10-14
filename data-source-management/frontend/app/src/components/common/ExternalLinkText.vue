<template>
  <span class="external-link-text">
    <span :class="{ 'text-weight-bold': boldText }">
      <slot>{{ text }}</slot>
    </span>
    <q-btn
      v-if="!hideButton"
      flat
      dense
      round
      size="xs"
      icon="open_in_new"
      color="grey-7"
      class="q-ml-xs"
      type="a"
      :href="href"
      target="_blank"
      rel="noopener noreferrer"
      :aria-label="tooltip"
    >
      <q-tooltip>{{ tooltip }}</q-tooltip>
    </q-btn>
  </span>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    href: string;
    text?: string;
    tooltip?: string;
    boldText?: boolean;
    hideButton?: boolean;
  }>(),
  {
    text: '',
    tooltip: 'Open in new tab',
    boldText: true,
    hideButton: false,
  },
);
</script>

<style scoped>
.external-link-text {
  font: inherit;
  color: inherit;
  letter-spacing: inherit;
}
</style>
