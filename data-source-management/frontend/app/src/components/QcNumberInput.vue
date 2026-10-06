<template>
  <q-input
    filled
    :model-value="model"
    :label="label"
    :hint="hint"
    :rules="rules"
    @update:model-value="(val) => (model = toNumberOrNull(val))"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
import type { ValidationRule } from 'quasar';
import { toNumberOrNull } from '@/utils/quality_control_function_utils';

defineProps<{
  label: string;
  hint?: string;
  rules?: Array<ValidationRule>;
}>();

const model = defineModel<number | null>();
</script>

<style scoped></style>
