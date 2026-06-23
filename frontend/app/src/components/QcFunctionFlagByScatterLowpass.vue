<template>
  <qc-function-form-template
    function-title="flagByScatterLowpass"
    @submit="submitForm"
    @remove="removeForm"
  >
    <!-- field        -->
    <div class="q-mb-md">
      <span class="text-bold block">Field *</span>
      <span class="text-caption text-grey block q-mb-sm"> Input Datastream(s). </span>
      <sta-datastream-input
        max-height="300px"
        :rules="[requiredDatastreamsRule]"
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
      />
    </div>

    <!--    window-->
    <qc-function-form-offset-input
      :rules="[requiredRule('window'), offsetAliasMatchRule]"
      class="q-mb-md"
      v-model="formData.window"
      label="window *"
      hint="Chunk size for evaluation."
    />
    <!--    thresh-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.thresh"
      label="thresh * (enter a floating point number)"
      :rules="[requiredRule('thresh'), numberGreaterThanEqualsRule(0)]"
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
      :rules="[offsetAliasMatchRule]"
      class="q-mb-md"
      v-model="formData.window"
      label="sub_window"
      hint="Window size for sub-chunks."
    />
    <!--    sub_thresh-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.sub_thresh"
      label="sub_thresh (enter a floating point number)"
      :rules="[numberGreaterThanEqualsRule(0)]"
      hint="Threshold for sub-chunk deviation."
    />
    <!--    min_periods-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.min_periods"
      label="min_periods (enter a integer number)"
      :rules="[integerRule, numberGreaterThanEqualsRule(0)]"
      hint="Minimum points required in a chunk."
    />
  </qc-function-form-template>
</template>

<script setup lang="ts">
import QcFunctionFormTemplate from 'components/QcFunctionFormTemplate.vue';
import {
  integerRule,
  numberGreaterThanEqualsRule,
  offsetAliasMatchRule,
  requiredDatastreamsRule,
  requiredRule,
} from 'src/utils/form_utils';
import StaDatastreamInput from 'components/StaDatastreamInput.vue';
import { computed, ref } from 'vue';
import type { QualityControlFunctionArgumentBase } from 'src/services/quality_control_setting/types';
import QcFunctionFormOffsetInput from 'components/QcFunctionFormOffsetInput.vue';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';

defineProps<{
  permission_group_id: number;
}>();

const emit = defineEmits(['submit', 'remove']);

const funcOptions: Array<string> = ['std', 'var', 'mad'];

const formData = ref({
  field: [],
  target: [],
  window: null,
  thresh: null,
  func: 'std',
  sub_window: null,
  sub_thresh: null,
  min_periods: null,
});

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

  // include required fields
  const returnArray: Array<QualityControlFunctionArgumentBase> = [
    fieldObject,
    windowObject,
    threshObject,
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
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
