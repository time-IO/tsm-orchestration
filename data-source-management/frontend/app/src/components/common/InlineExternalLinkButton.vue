<template>
  <q-btn
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
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    href: string;
    tooltip?: string;
  }>(),
  {
    tooltip: "Open in new tab"
  },
);
</script>
