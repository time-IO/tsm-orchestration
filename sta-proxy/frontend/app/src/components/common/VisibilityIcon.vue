<template>
  <q-icon :name="definition.icon" :color="color ?? definition.color" :size="size">
    <q-tooltip v-if="tooltip">{{ definition.label }}</q-tooltip>
  </q-icon>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { VISIBILITIES, type VisibilityName } from '@/utils/visibility';

const props = withDefaults(
  defineProps<{
    visibility: VisibilityName;
    color?: string;
    size?: string;
    tooltip?: boolean;
  }>(),
  {
    size: 'sm',
    tooltip: true,
  },
);

const definition = computed(() => VISIBILITIES[props.visibility]);
</script>
