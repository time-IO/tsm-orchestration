<template>
  <q-icon name="info" class="cursor-pointer" @click.stop="openSaqcDocuForFunction(label)">
    <q-tooltip>Open SaQC Documentation</q-tooltip>
  </q-icon>
</template>

<script setup lang="ts">
import { openSaqcDocuForFunction } from 'src/utils/quality_control_utils';

defineProps<{
  label: string;
}>();
</script>
