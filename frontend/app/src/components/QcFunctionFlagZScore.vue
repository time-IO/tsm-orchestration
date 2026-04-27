<template>
  <qc-function-form-template function-title="flagZScore" @submit="submitForm" @remove="removeForm">
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
    <!--    method-->
    <q-select
      v-model="formData.method"
      :options="methodOptions"
      clearable
      class="q-mb-md"
      label="method"
      hint="'standard' or 'modified' Z-score calculation."
      filled
    />
    <!--    window-->
    <qc-function-form-int-offset-input
      label="window * "
      class="q-mb-md"
      :rules_int="[integerRule, numberGreaterThanEqualsRule(1)]"
      :rules_offset="[offsetAliasMatchRule]"
      v-model:current_type="current_window_type"
      v-model:input="formData.window"
      hint="Rolling window size."
    />
    <!--    thresh-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.thresh"
      label="thresh * (enter a floating point number)"
      :rules="[numberGreaterThanEqualsRule(0)]"
      hint="Z-score threshold."
    />
    <!--    min_residuals-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.min_residuals"
      label="min_residuals * (enter a floating point number)"
      :rules="[numberGreaterThanEqualsRule(0)]"
      hint="Minimum residual to consider a point as outlier."
    />
    <!--    min_periods-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.min_periods"
      label="min_periods (enter a integer number)"
      :rules="[integerRule, numberGreaterThanEqualsRule(1)]"
      hint="Minimum valid points in a window."
    />
    <!--    center-->
    <div class="q-mb-md">
      <q-item tag="label" v-ripple>
        <q-item-section avatar>
          <q-toggle v-model="formData.center" />
        </q-item-section>
        <q-item-section>
          <q-item-label>center</q-item-label>
          <q-item-label caption>Whether to center the window.</q-item-label>
        </q-item-section>
      </q-item>
    </div>
    <!--    axis-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.axis"
      label="axis (enter a integer number)"
      :rules="[integerRule, numberGreaterThanEqualsRule(0), numberLowerThanEqualsRule(1)]"
      hint="Axis along which scoring is applied."
    />
  </qc-function-form-template>
</template>

<script setup lang="ts">
import QcFunctionFormTemplate from 'components/QcFunctionFormTemplate.vue';
import {
  integerRule,
  numberGreaterThanEqualsRule,
  numberLowerThanEqualsRule,
  offsetAliasMatchRule,
  requiredDatastreamsRule,
} from 'src/utils/form_utils';
import StaDatastreamInput from 'components/StaDatastreamInput.vue';
import { computed, ref } from 'vue';
import type { QualityControlFunctionArgumentBase } from 'src/services/quality_control_setting/types';
import QcFunctionFormIntOffsetInput from 'components/QcFunctionFormIntOffsetInput.vue';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';

defineProps<{
  permission_group_id: number;
}>();

const emit = defineEmits(['submit', 'remove']);
const current_window_type = ref(POSSIBLE_QC_FUNCTION_TYPES.INT);

const methodOptions: Array<string> = ['standard', 'modified'];

const formData = ref({
  field: [],
  target: [],
  method: null,
  window: null,
  thresh: null,
  min_residuals: null,
  min_periods: null,
  center: true,
  axis: null,
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
  const methodObject = {
    name: 'method',
    input: { value: formData.value.method },
    type: POSSIBLE_QC_FUNCTION_TYPES.ENUM,
  };
  const windowObject = {
    name: 'window',
    input: { value: formData.value.window },
    type: current_window_type.value,
  };
  const threshObject = {
    name: 'thresh',
    input: { value: formData.value.thresh },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };
  const min_residualsObject = {
    name: 'min_residuals',
    input: { value: formData.value.min_residuals },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };
  const min_periodsObject = {
    name: 'min_periods',
    input: { value: formData.value.min_periods },
    type: POSSIBLE_QC_FUNCTION_TYPES.INT,
  };
  const centerObject = {
    name: 'center',
    input: { value: formData.value.center },
    type: POSSIBLE_QC_FUNCTION_TYPES.BOOL,
  };
  const axisObject = {
    name: 'axis',
    input: { value: formData.value.axis },
    type: POSSIBLE_QC_FUNCTION_TYPES.INT,
  };

  // include required fields
  const returnArray: Array<QualityControlFunctionArgumentBase> = [fieldObject];

  // only add optional fields if their value is not null
  if (formData.value.target.length > 0) {
    returnArray.push(targetObject);
  }
  if (formData.value.method !== null) {
    returnArray.push(methodObject);
  }
  if (formData.value.window !== null) {
    returnArray.push(windowObject);
  }
  if (formData.value.thresh !== null) {
    returnArray.push(threshObject);
  }
  if (formData.value.min_residuals !== null) {
    returnArray.push(min_residualsObject);
  }
  if (formData.value.min_periods !== null) {
    returnArray.push(min_periodsObject);
  }
  if (formData.value.axis !== null) {
    returnArray.push(axisObject);
  }
  if (formData.value.center !== null) {
    returnArray.push(centerObject);
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
  formData.value.method = null;
  formData.value.window = null;
  formData.value.thresh = null;
  formData.value.min_residuals = null;
  formData.value.min_periods = null;
  formData.value.center = true;
  formData.value.axis = null;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
