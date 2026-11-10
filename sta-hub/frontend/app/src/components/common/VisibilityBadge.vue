<template>
  <q-badge :color="color ?? definition.color" class="visibility-badge">
    <visibility-icon :visibility="visibility" color="white" size="xs" :tooltip="false" />
    <span class="q-ml-xs">{{ definition.label }}</span>
  </q-badge>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import VisibilityIcon from '@/components/common/VisibilityIcon.vue';
import { VISIBILITIES, type VisibilityName } from '@/utils/visibility';

const props = defineProps<{
  visibility: VisibilityName;
  color?: string;
}>();

const definition = computed(() => VISIBILITIES[props.visibility]);
</script>

<style scoped>
.visibility-badge {
  padding: 4px 8px;
}
</style>
