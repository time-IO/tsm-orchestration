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

    <!--        tolerance-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.tolerance"
      label="tolerance * (enter a floating point number)"
      :rules="[requiredRule('tolerance'), numberGreaterThanEqualsRule(0)]"
      hint="Maximum allowed difference between preceding and succeeding values."
    />

    <!--        window-->
    <qc-function-form-offset-input
      :rules="[requiredRule('window'), offsetAliasMatchRule]"
      class="q-mb-md"
      v-model="formData.window"
      label="window *"
      hint="Maximum duration for the offset sequence."
    />

    <!--        thresh-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.thresh"
      label="thresh (enter a floating point number)"
      :rules="[numberGreaterThanEqualsRule(0)]"
      hint="Minimum absolute difference to consider a sequence as an offset."
    />

    <!--        thresh_relative-->

    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.thresh_relative"
      label="thresh_relative (enter a floating point number)"
      hint="Minimum relative change to consider a sequence as an offset."
    />
  </qc-function-form-template>
</template>

<script setup lang="ts">
import {
  numberGreaterThanEqualsRule,
  offsetAliasMatchRule,
  requiredDatastreamsRule,
  requiredRule,
} from 'src/utils/form_utils';
import StaDatastreamInput from 'components/StaDatastreamInput.vue';
import { computed, ref } from 'vue';
import QcFunctionFormOffsetInput from 'components/QcFunctionFormOffsetInput.vue';
import type { QualityControlFunctionArgumentBase } from 'src/services/quality_control_setting/types';
import QcFunctionFormTemplate from 'components/QcFunctionFormTemplate.vue';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';

defineProps<{
  permission_group_id: number;
}>();

const formData = ref({
  field: [],
  target: [],
  tolerance: null,
  window: null,
  thresh: null,
  thresh_relative: null,
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
  const toleranceObject = {
    name: 'tolerance',
    input: { value: formData.value.tolerance },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
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
  const thresh_relativeObject = {
    name: 'thresh_relative',
    input: { value: formData.value.thresh_relative },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };

  // include required fields
  const returnArray: Array<QualityControlFunctionArgumentBase> = [
    fieldObject,
    windowObject,
    toleranceObject,
  ];

  // only add optional fields if their value is not null
  if (formData.value.target.length > 0) {
    returnArray.push(targetObject);
  }
  if (formData.value.thresh !== null) {
    returnArray.push(threshObject);
  }
  if (formData.value.thresh_relative !== null) {
    returnArray.push(thresh_relativeObject);
  }

  return returnArray;
});

const emit = defineEmits(['submit', 'remove']);

const submitForm = () => {
  emit('submit', formDataWithTypes.value);
  resetFormData();
};

const resetFormData = () => {
  formData.value.field = [];
  formData.value.target = [];
  formData.value.tolerance = null;
  formData.value.window = null;
  formData.value.thresh = null;
  formData.value.thresh_relative = null;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
