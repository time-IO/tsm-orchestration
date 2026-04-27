<template>
  <qc-function-form-template function-title="flagJumps" @submit="submitForm" @remove="removeForm">
    <!-- field        -->
    <div class="q-mb-md">
      <span class="text-bold block">Field *</span>
      <span class="text-caption text-grey block q-mb-sm"> Input data stream(s). </span>
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
        Output data stream(s) to which the results are written. Defaults to field if null.
      </span>
      <sta-datastream-input
        max-height="300px"
        v-model="formData.target"
        :permission_group_id="permission_group_id"
      />
    </div>

    <!-- thresh        -->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.thresh"
      label="thresh * (enter a floating point number)"
      :rules="[requiredRule('thresh'), numberGreaterThanEqualsRule(0)]"
      hint="Threshold for mean difference between adjacent windows to trigger flagging."
    />

    <!-- window        -->

    <qc-function-form-offset-input
      :rules="[requiredRule('window'), offsetAliasMatchRule]"
      class="q-mb-md"
      v-model="formData.window"
      label="window *"
      hint="Size of the rolling windows used to calculate the mean."
    />

    <!-- min_periods        -->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.min_periods"
      label="min_periods (enter a integer number)"
      :rules="[integerRule, numberGreaterThanEqualsRule(0)]"
      hint="Minimum observations required for a valid mean calculation."
    />
  </qc-function-form-template>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import {
  requiredRule,
  offsetAliasMatchRule,
  integerRule,
  numberGreaterThanEqualsRule,
  requiredDatastreamsRule,
} from 'src/utils/form_utils';
import type { QualityControlFunctionArgumentBase } from 'src/services/quality_control_setting/types';
import StaDatastreamInput from 'components/StaDatastreamInput.vue';
import QcFunctionFormOffsetInput from 'components/QcFunctionFormOffsetInput.vue';
import QcFunctionFormTemplate from 'components/QcFunctionFormTemplate.vue';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';

defineProps<{
  permission_group_id: number;
}>();

const formData = ref({
  field: [],
  target: [],
  thresh: null,
  window: null,
  min_periods: null,
});

const emit = defineEmits(['submit', 'remove']);

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
  const threshObject = {
    name: 'thresh',
    input: { value: formData.value.thresh },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };
  const windowObject = {
    name: 'window',
    input: { value: formData.value.window },
    type: POSSIBLE_QC_FUNCTION_TYPES.OFFSET,
  };
  const min_periodsObject = {
    name: 'min_periods',
    input: { value: formData.value.min_periods },
    type: POSSIBLE_QC_FUNCTION_TYPES.INT,
  };

  // include required fields
  const returnArray: Array<QualityControlFunctionArgumentBase> = [
    fieldObject,
    threshObject,
    windowObject,
  ];

  // only add optional fields if their value is not null
  if (formData.value.target.length > 0) {
    returnArray.push(targetObject);
  }
  if (formData.value.min_periods !== null) {
    returnArray.push(min_periodsObject);
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
  formData.value.thresh = null;
  formData.value.window = null;
  formData.value.min_periods = null;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
