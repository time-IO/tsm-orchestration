<template>
  <q-input
    v-if="current_type === POSSIBLE_QC_FUNCTION_TYPES.FLOAT"
    v-model.number="input"
    filled
    :label="`${label} (enter a floating point number)`"
    :rules="rules_float"
    :hint="hint_float"
    v-bind="$attrs"
  >
    <template v-slot:after>
      <q-btn round icon="sync_alt" @click="change_type_to(POSSIBLE_QC_FUNCTION_TYPES.INT)">
        <q-tooltip> Change type </q-tooltip>
      </q-btn>
    </template>
  </q-input>
  <q-input
    v-if="current_type === POSSIBLE_QC_FUNCTION_TYPES.INT"
    v-model.number="input"
    filled
    :label="`${label} (enter a integer number)`"
    :rules="rules_int"
    :hint="hint_int"
    v-bind="$attrs"
  >
    <template v-slot:after>
      <q-btn round icon="sync_alt" @click="change_type_to(POSSIBLE_QC_FUNCTION_TYPES.FLOAT)">
        <q-tooltip> Change type </q-tooltip>
      </q-btn>
    </template>
  </q-input>
</template>

<script setup lang="ts">
import type { ValidationRule } from 'quasar';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';

defineProps<{
  label: string;
  rules_float: Array<ValidationRule>;
  rules_int: Array<ValidationRule>;
  hint_float: string;
  hint_int: string;
}>();

const current_type = defineModel('current_type');
const input = defineModel<number | null>('input');

const change_type_to = (type: string) => {
  current_type.value = type;
};
</script>

<style scoped></style>
