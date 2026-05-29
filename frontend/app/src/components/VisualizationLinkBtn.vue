<template>
  <q-btn
    v-if="visualizationUrl"
    flat
    dense
    no-caps
    size="sm"
    class="q-ml-sm q-pa-none"
    icon-right="launch"
    color="primary"
    :href="visualizationUrl"
    target="_blank"
    rel="noopener noreferrer"
  >
    Open Visualization
  </q-btn>
</template>

<script lang="ts" setup>
import { computed } from 'vue';

const props = defineProps<{
  uuid?: string | null;
}>();

const visualizationUrl = computed(() => {
  if (!props.uuid) {
    return '';
  }

  return `${window.location.origin}/visualization/d/${encodeURIComponent(props.uuid)}?orgId=1`;
});
</script>
