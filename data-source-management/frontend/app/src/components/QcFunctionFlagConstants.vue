<template>
  <qc-function-form-template
    function-title="flagConstants"
    v-model:label="label"
    @submit="submitForm"
    @remove="removeForm"
  >
    <!-- field        -->
    <div class="q-mb-md">
      <span class="text-bold block">Field *</span>
      <span class="text-caption text-grey block q-mb-sm"> Input data stream to process. </span>
      <sta-datastream-input
        max-height="300px"
        :rules="[rules.LIST, ruleFactories.MIN(1)]"
        v-model="formData.field"
        :permission_group_id="permission_group_id"
      />
    </div>

    <!-- target        -->
    <div class="q-mb-md">
      <span class="text-bold block">Target</span>
      <span class="text-caption text-grey block q-mb-sm">
        Output data stream to which the results are written. Defaults to field if null.
      </span>
      <sta-datastream-input
        max-height="300px"
        v-model="formData.target"
        :permission_group_id="permission_group_id"
        :showTempCreateBtn="true"
      />
    </div>

    <!-- window        -->
    <div class="q-mb-md">
      <q-input filled v-model="formData.window" :rules="[rules.REQUIRED]" label="Window *" />
      <span class="text-caption text-grey block">
        Size of the rolling window. Either an integer (number of timestamps per window) or an
        offset string (e.g. '3h') for the window's total temporal extent.
      </span>
    </div>

    <!-- thresh     -->
    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.thresh"
      :rules="[rules.FLOAT, ruleFactories.MIN(0)]"
      label="thresh"
      hint="Maximum total change allowed per window."
    />

    <!-- min_periods     -->
    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.min_periods"
      :rules="[rules.INTEGER, ruleFactories.MIN(2)]"
      label="min_periods"
      hint="Minimum number of valid timestamps required per window (>= 2)."
    />

    <!-- flag     -->
    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.flag"
      label="Flag (enter a floating point number)"
      :rules="[ruleFactories.MIN(0)]"
      hint="Flag assigned to values identified by this function."
    />

    <!-- dfilter    -->
    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.dfilter"
      :rules="[rules.FLOAT]"
      label="dfilter (enter a floating point number)"
      hint="Values with flags greater than or equal to this threshold are treated as missing during processing."
    />
  </qc-function-form-template>
</template>

<script setup lang="ts">
import QcFunctionFormTemplate from '@/components/QcFunctionFormTemplate.vue';
import StaDatastreamInput from '@/components/StaDatastreamInput.vue';
import { computed, ref, watch } from 'vue';
import type { QualityControlFunctionArgumentBase } from '@/services/quality_control_setting/types';
import { POSSIBLE_QC_FUNCTION_TYPES } from '@/utils/quality_control_utils';
import type { Datastream } from '@/services/sta/types';
import { ruleFactories, rules } from '@/utils/validation/rules';

const props = defineProps<{
  permission_group_id: number;
  initialData?: QualityControlFunctionArgumentBase[];
}>();

const label = defineModel<string | undefined>('label');
const emit = defineEmits(['submit', 'remove']);

const formData = ref({
  field: [] as Datastream[],
  target: [] as Datastream[],
  window: '',
  thresh: 0,
  min_periods: 2,
  flag: 255.0,
  dfilter: 0,
});

function loadInitialData() {
  if (!props.initialData) return;

  const fieldArg = props.initialData.find((a) => a.name === 'field');
  const targetArg = props.initialData.find((a) => a.name === 'target');
  const windowArg = props.initialData.find((a) => a.name === 'window');
  const threshArg = props.initialData.find((a) => a.name === 'thresh');
  const minPeriodsArg = props.initialData.find((a) => a.name === 'min_periods');
  const flagArg = props.initialData.find((a) => a.name === 'flag');
  const dfilterArg = props.initialData.find((a) => a.name === 'dfilter');

  formData.value.field = (fieldArg?.input.value as Datastream[]) ?? [];
  formData.value.target = (targetArg?.input.value as Datastream[]) ?? [];
  formData.value.window = String((windowArg?.input.value as string | number) ?? '');
  formData.value.thresh = (threshArg?.input.value as number) ?? 0;
  formData.value.min_periods = (minPeriodsArg?.input.value as number) ?? 2;
  formData.value.flag = (flagArg?.input.value as number) ?? 255;
  formData.value.dfilter = (dfilterArg?.input.value as number) ?? null;
}
watch(() => props.initialData, loadInitialData, { immediate: true });

const formDataWithTypes = computed(() => {
  const fieldObject = {
    name: 'field',
    input: { value: formData.value.field },
    type: POSSIBLE_QC_FUNCTION_TYPES.DATASTREAM,
  };
  const targetObject = {
    name: 'target',
    // optional -> leeres Array darf NICHT gesendet werden (verletzt min:1),
    // stattdessen bei fehlender Auswahl null senden
    input: { value: formData.value.target.length > 0 ? formData.value.target : null },
    type: POSSIBLE_QC_FUNCTION_TYPES.DATASTREAM,
  };
  const windowIsPlainCount = /^\d+$/.test(formData.value.window.trim());
  const windowObject = {
    name: 'window',
    // reine Zahl -> als int senden, sonst als offset-String (z.B. '3h')
    input: {
      value: windowIsPlainCount ? Number(formData.value.window) : formData.value.window,
    },
    // TODO prüfen: passende Type-Konstanten für int/offset (s. Hinweis im Chat)
    type: windowIsPlainCount ? POSSIBLE_QC_FUNCTION_TYPES.INT : POSSIBLE_QC_FUNCTION_TYPES.STR,
  };
  const threshObject = {
    name: 'thresh',
    input: { value: formData.value.thresh },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };
  const minPeriodsObject = {
    name: 'min_periods',
    input: { value: formData.value.min_periods },
    // TODO prüfen: passender Type-Konstante für Integer (s. Hinweis im Chat)
    type: POSSIBLE_QC_FUNCTION_TYPES.INT,
  };
  const flagObject = {
    name: 'flag',
    input: { value: formData.value.flag },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };
  const dfilterObject = {
    name: 'dfilter',
    input: { value: formData.value.dfilter },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };

  // include required fields
  const returnArray: Array<QualityControlFunctionArgumentBase> = [
    fieldObject,
    targetObject,
    windowObject,
    threshObject,
    minPeriodsObject,
    flagObject,
    dfilterObject,
  ];

  return returnArray;
});

const submitForm = () => {
  emit('submit', formDataWithTypes.value);
  resetFormData();
};

const resetFormData = () => {
  formData.value.field = [];
  formData.value.target = [];
  formData.value.window = '';
  formData.value.thresh = 0;
  formData.value.min_periods = 2;
  formData.value.flag = 255.0;
  formData.value.dfilter = 0;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
