<template>
  <qc-function-form-template
    function-title="flagIsolated"
    @submit="submitForm"
    @remove="removeForm"
  >
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

    <!-- gap_window        -->

    <qc-function-form-offset-input
      :rules="[requiredRule('gap_window'), offsetAliasMatchRule]"
      class="q-mb-md"
      v-model="formData.gap_window"
      label="gap_window *"
      hint="Minimum gap size required before and after a group to consider it isolated."
    />

    <!-- group_window        -->

    <qc-function-form-offset-input
      :rules="[requiredRule('group_window'), offsetAliasMatchRule]"
      class="q-mb-md"
      v-model="formData.group_window"
      label="group_window *"
      hint="Maximum size of a data chunk to consider for isolation."
    />
  </qc-function-form-template>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { requiredRule, offsetAliasMatchRule, requiredDatastreamsRule } from 'src/utils/form_utils';
import StaDatastreamInput from 'components/StaDatastreamInput.vue';
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
  gap_window: null,
  group_window: null,
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
  const gap_windowObject = {
    name: 'gap_window',
    input: { value: formData.value.gap_window },
    type: POSSIBLE_QC_FUNCTION_TYPES.OFFSET,
  };
  const group_windowObject = {
    name: 'group_window',
    input: { value: formData.value.group_window },
    type: POSSIBLE_QC_FUNCTION_TYPES.OFFSET,
  };

  // include required fields
  const returnArray: Array<QualityControlFunctionArgumentBase> = [
    fieldObject,
    gap_windowObject,
    group_windowObject,
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
  formData.value.gap_window = null;
  formData.value.group_window = null;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
