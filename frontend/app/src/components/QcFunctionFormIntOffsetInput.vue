<template>
  <q-input
    v-if="current_type === POSSIBLE_QC_FUNCTION_TYPES.INT"
    v-model="input"
    filled
    :label="`${label} (enter a integer number)`"
    :rules="rules_int"
    :hint="hint"
    v-bind="$attrs"
  >
    <template v-slot:after>
      <q-btn round icon="sync_alt" @click="change_type_to(POSSIBLE_QC_FUNCTION_TYPES.OFFSET)">
        <q-tooltip> Change type </q-tooltip>
      </q-btn>
    </template>
  </q-input>
  <qc-function-form-offset-input
    v-else-if="current_type === POSSIBLE_QC_FUNCTION_TYPES.OFFSET"
    v-model="input"
    :label="`${label}`"
    :rules="rules_offset"
    :hint="hint"
    v-bind="$attrs"
  >
    <template v-slot:after>
      <q-btn round icon="sync_alt" @click="change_type_to(POSSIBLE_QC_FUNCTION_TYPES.INT)">
        <q-tooltip> Change type </q-tooltip>
      </q-btn>
    </template>
  </qc-function-form-offset-input>
</template>

<script setup lang="ts">
import type { ValidationRule } from 'quasar';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';
import QcFunctionFormOffsetInput from 'components/QcFunctionFormOffsetInput.vue';

defineProps<{
  label: string;
  rules_int: Array<ValidationRule>;
  rules_offset: Array<ValidationRule>;
  hint: string;
}>();

const current_type = defineModel('current_type');
const input = defineModel<number | null>('input', { default: null });

const change_type_to = (type: string) => {
  current_type.value = type;
};
</script>

<style scoped></style>
