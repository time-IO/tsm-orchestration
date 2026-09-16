<template>
  <qc-function-form-template
    function-title="flagByScatterLowpass"
    v-model:label="label"
    @submit="submitForm"
    @remove="removeForm"
  >
    <!-- field        -->
    <div class="q-mb-md">
      <span class="text-bold block">Field *</span>
      <span class="text-caption text-grey block q-mb-sm"> Input Datastream(s). </span>
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
        Output Datastream(s) to which the results are written. Defaults to field if null.
      </span>
      <sta-datastream-input
        max-height="300px"
        v-model="formData.target"
        :permission_group_id="permission_group_id"
        :showTempCreateBtn="true"
      />
    </div>

    <!--    window-->
    <qc-function-form-offset-input
      :rules="[rules.REQUIRED, rules.CONTEXT_WINDOW]"
      class="q-mb-md"
      v-model="formData.window"
      label="window *"
      hint="Chunk size for evaluation."
    />
    <!--    thresh-->
    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.thresh"
      label="thresh * (enter a floating point number)"
      :rules="[rules.REQUIRED, ruleFactories.MIN(0)]"
      hint="Threshold for chunk deviation."
    />
    <!--    func-->
    <q-select
      v-model="formData.func"
      :options="funcOptions"
      class="q-mb-md"
      label="func"
      hint="Aggregation function for chunk evaluation."
      filled
      clearable
    />
    <!--    sub_window-->
    <qc-function-form-offset-input
      :rules="[rules.CONTEXT_WINDOW]"
      class="q-mb-md"
      v-model="formData.sub_window"
      label="sub_window"
      hint="Window size for sub-chunks."
    />
    <!--    sub_thresh-->
    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.sub_thresh"
      label="sub_thresh (enter a floating point number)"
      :rules="[rules.FLOAT, ruleFactories.MIN(0)]"
      hint="Threshold for sub-chunk deviation."
    />
    <!--    min_periods-->
    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.min_periods"
      label="min_periods (enter a integer number)"
      :rules="[rules.INTEGER, ruleFactories.MIN(0)]"
      hint="Minimum points required in a chunk."
    />
    <!-- flag     -->
    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.flag"
      label="Flag"
      :rules="[ruleFactories.MIN(0)]"
      hint="Enter a floating point number"
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
import QcFunctionFormTemplate from 'components/QcFunctionFormTemplate.vue';
import StaDatastreamInput from 'components/StaDatastreamInput.vue';
import { computed, ref, watch } from 'vue';
import type { QualityControlFunctionArgumentBase } from 'src/services/quality_control_setting/types';
import QcFunctionFormOffsetInput from 'components/QcFunctionFormOffsetInput.vue';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';
import type { Datastream } from 'src/services/sta/types';
import { ruleFactories, rules } from 'src/utils/validation/rules';

const props = defineProps<{
  permission_group_id: number;
  initialData?: QualityControlFunctionArgumentBase[];
}>();

const label = defineModel<string | undefined>('label');
const emit = defineEmits(['submit', 'remove']);

const funcOptions: Array<string> = ['std', 'var', 'mad'];

const formData = ref({
  field: [] as Datastream[],
  target: [] as Datastream[],
  window: null as number | null,
  thresh: null as number | null,
  func: 'std',
  sub_window: null as number | null,
  sub_thresh: null as number | null,
  min_periods: null as number | null,
  flag: 255.0 as number | null,
  dfilter: 0 as number | null,
});

function loadInitialData() {
  if (!props.initialData) return;

  const fieldArg = props.initialData.find((a) => a.name === 'field');
  const targetArg = props.initialData.find((a) => a.name === 'target');
  const windowArg = props.initialData.find((a) => a.name === 'window');
  const threshArg = props.initialData.find((a) => a.name === 'thresh');
  const funcArg = props.initialData.find((a) => a.name === 'func');
  const subWindowArg = props.initialData.find((a) => a.name === 'sub_window');
  const subThreshArg = props.initialData.find((a) => a.name === 'sub_thresh');
  const minPeriodsArg = props.initialData.find((a) => a.name === 'min_periods');
  const flagArg = props.initialData.find((a) => a.name === 'flag');
  const dfilterArg = props.initialData.find((a) => a.name === 'dfilter');

  formData.value.field = (fieldArg?.input.value as Datastream[]) ?? [];
  formData.value.target = (targetArg?.input.value as Datastream[]) ?? [];
  formData.value.window = (windowArg?.input.value as number) ?? null;
  formData.value.thresh = (threshArg?.input.value as number) ?? null;
  formData.value.func = (funcArg?.input.value as string) ?? 'std';
  formData.value.sub_window = (subWindowArg?.input.value as number) ?? null;
  formData.value.sub_thresh = (subThreshArg?.input.value as number) ?? null;
  formData.value.min_periods = (minPeriodsArg?.input.value as number) ?? null;
  formData.value.flag = (flagArg?.input.value as number) ?? null;
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
    input: { value: formData.value.target },
    type: POSSIBLE_QC_FUNCTION_TYPES.DATASTREAM,
  };
  const windowObject = {
    name: 'window',
    input: { value: formData.value.window },
    type: POSSIBLE_QC_FUNCTION_TYPES.OFFSET,
  };
  const threshObject = {
    name: 'thresh',
    input: { value: formData.value.thresh },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };
  const funcObject = {
    name: 'func',
    input: { value: formData.value.func },
    type: POSSIBLE_QC_FUNCTION_TYPES.ENUM,
  };
  const sub_windowObject = {
    name: 'sub_window',
    input: { value: formData.value.sub_window },
    type: POSSIBLE_QC_FUNCTION_TYPES.OFFSET,
  };
  const sub_threshObject = {
    name: 'sub_thresh',
    input: { value: formData.value.sub_thresh },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };
  const min_periodsObject = {
    name: 'min_periods',
    input: { value: formData.value.min_periods },
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
    windowObject,
    threshObject,
    flagObject,
    dfilterObject,
  ];

  // only add optional fields if their value is not null
  if (formData.value.target.length > 0) {
    returnArray.push(targetObject);
  }
  if (formData.value.sub_window !== null) {
    returnArray.push(sub_windowObject);
  }
  if (formData.value.sub_thresh !== null) {
    returnArray.push(sub_threshObject);
  }
  if (formData.value.min_periods !== null) {
    returnArray.push(min_periodsObject);
  }
  if (formData.value.func !== null) {
    returnArray.push(funcObject);
  }

  return returnArray;
});

const submitForm = () => {
  emit('submit', formDataWithTypes.value);
  resetFormData();
};

const resetFormData = () => {
  formData.value.field = [];
  formData.value.target = [];
  formData.value.window = null;
  formData.value.thresh = null;
  formData.value.func = 'std';
  formData.value.sub_window = null;
  formData.value.sub_thresh = null;
  formData.value.min_periods = null;
  formData.value.flag = 255.0;
  formData.value.dfilter = 0;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
