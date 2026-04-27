<template>
  <qc-function-form-template function-title="flagRange" @submit="submitForm" @remove="removeForm">
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

    <!--        min-->

    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.min"
      :rules="[requiredRule('min')]"
      label="min * (enter a floating point number)"
      hint="Lower bound for valid data."
    />

    <!--    max-->
    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.max"
      :rules="[requiredRule('max')]"
      label="max * (enter a floating point number)"
      hint="Upper bound for valid data."
    />
  </qc-function-form-template>
</template>

<script setup lang="ts">
import QcFunctionFormTemplate from 'components/QcFunctionFormTemplate.vue';
import { requiredDatastreamsRule, requiredRule } from 'src/utils/form_utils';
import StaDatastreamInput from 'components/StaDatastreamInput.vue';
import { computed, ref } from 'vue';
import type { QualityControlFunctionArgumentBase } from 'src/services/quality_control_setting/types';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';

defineProps<{
  permission_group_id: number;
}>();

const emit = defineEmits(['submit', 'remove']);

const formData = ref({
  field: [],
  target: [],
  min: null,
  max: null,
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
  const minObject = {
    name: 'min',
    input: { value: formData.value.min },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };
  const maxObject = {
    name: 'max',
    input: { value: formData.value.max },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };

  // include required fields
  const returnArray: Array<QualityControlFunctionArgumentBase> = [
    fieldObject,
    minObject,
    maxObject,
  ];

  // only add optional fields if their value is not null
  if (formData.value.target.length > 0) {
    returnArray.push(targetObject);
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
  formData.value.min = null;
  formData.value.max = null;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
