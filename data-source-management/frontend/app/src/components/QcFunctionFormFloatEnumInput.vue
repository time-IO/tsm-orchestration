<template>
  <q-input
    v-if="current_type === POSSIBLE_QC_FUNCTION_TYPES.FLOAT"
    v-model.number="input"
    filled
    :label="`${label} (enter a floating point number)`"
    :rules="rules_float"
    :hint="hint"
    v-bind="$attrs"
  >
    <template v-slot:after>
      <q-btn round icon="sync_alt" @click="change_type_to(POSSIBLE_QC_FUNCTION_TYPES.ENUM)">
        <q-tooltip> Change type </q-tooltip>
      </q-btn>
    </template>
  </q-input>
  <q-select
    v-if="current_type === POSSIBLE_QC_FUNCTION_TYPES.ENUM"
    v-model="input"
    :options="enumOptions"
    :label="label"
    filled
    :hint="hint"
    :rules="rules_enum"
    v-bind="$attrs"
  >
    <template v-slot:after>
      <q-btn round icon="sync_alt" @click="change_type_to(POSSIBLE_QC_FUNCTION_TYPES.FLOAT)">
        <q-tooltip> Change type </q-tooltip>
      </q-btn>
    </template>
  </q-select>
</template>

<script setup lang="ts">
import type { ValidationRule } from 'quasar';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';

defineProps<{
  label: string;
  rules_float: Array<ValidationRule>;
  rules_enum: Array<ValidationRule>;
  hint: string;
  enumOptions: Array<string>;
}>();

const current_type = defineModel('current_type');
const input = defineModel<string | number>('input');

const change_type_to = (type: string) => {
  current_type.value = type;
};
</script>

<style scoped></style>
