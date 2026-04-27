<template>
  <qc-function-form-template function-title="flagPlateau" @submit="submitForm" @remove="removeForm">
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

    <!-- min_length        -->
    <qc-function-form-int-offset-input
      label="min_length * "
      class="q-mb-md"
      :rules_int="[requiredRule('min_length'), integerRule, numberGreaterThanEqualsRule(1)]"
      :rules_offset="[requiredRule('min_length'), offsetAliasMatchRule]"
      v-model:current_type="current_min_length_type"
      v-model:input="formData.min_length"
      hint="Minimum temporal extension of a plateau."
    />

    <!-- max_length        -->
    <qc-function-form-int-offset-input
      label="max_length"
      class="q-mb-md"
      :rules_int="[integerRule, numberGreaterThanEqualsRule(1)]"
      :rules_offset="[offsetAliasMatchRule]"
      v-model:current_type="current_max_length_type"
      v-model:input="formData.max_length"
      hint="Maximum temporal extension of a plateau."
    />

    <!-- min_jump        -->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.min_jump"
      label="min_jump (enter a floating point number)"
      :rules="[numberGreaterThanEqualsRule(0)]"
      hint="Minimum difference from preceding/succeeding periods."
    />

    <!-- granularity        -->

    <qc-function-form-int-offset-input
      label="granularity"
      class="q-mb-md"
      :rules_int="[integerRule, numberGreaterThanEqualsRule(1)]"
      :rules_offset="[offsetAliasMatchRule]"
      v-model:current_type="current_granularity_type"
      v-model:input="formData.granularity"
      hint="Precision of the search."
    />
  </qc-function-form-template>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import StaDatastreamInput from 'components/StaDatastreamInput.vue';
import {
  requiredRule,
  offsetAliasMatchRule,
  requiredDatastreamsRule,
  integerRule,
  numberGreaterThanEqualsRule,
} from 'src/utils/form_utils';
import QcFunctionFormIntOffsetInput from 'components/QcFunctionFormIntOffsetInput.vue';
import type { QualityControlFunctionArgumentBase } from 'src/services/quality_control_setting/types';
import QcFunctionFormTemplate from 'components/QcFunctionFormTemplate.vue';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';

defineProps<{
  permission_group_id: number;
}>();

const current_min_length_type = ref(POSSIBLE_QC_FUNCTION_TYPES.INT);
const current_max_length_type = ref(POSSIBLE_QC_FUNCTION_TYPES.INT);
const current_granularity_type = ref(POSSIBLE_QC_FUNCTION_TYPES.INT);

const formData = ref({
  field: [],
  target: [],
  min_length: null,
  max_length: null,
  min_jump: null,
  granularity: null,
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
  const min_lengthObject = {
    name: 'min_length',
    input: { value: formData.value.min_length },
    type: current_min_length_type.value,
  };
  const max_lengthObject = {
    name: 'max_length',
    input: { value: formData.value.max_length },
    type: current_max_length_type.value,
  };
  const min_jumpObject = {
    name: 'min_jump',
    input: { value: formData.value.min_jump },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };
  const granularityObject = {
    name: 'granularity',
    input: { value: formData.value.granularity },
    type: current_granularity_type.value,
  };

  // include required fields
  const returnArray: Array<QualityControlFunctionArgumentBase> = [fieldObject, min_lengthObject];

  // only add optional fields if their value is not null
  if (formData.value.target.length > 0) {
    returnArray.push(targetObject);
  }
  if (formData.value.max_length !== null) {
    returnArray.push(max_lengthObject);
  }
  if (formData.value.min_jump !== null) {
    returnArray.push(min_jumpObject);
  }
  if (formData.value.granularity !== null) {
    returnArray.push(granularityObject);
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
  formData.value.max_length = null;
  formData.value.min_length = null;
  formData.value.min_jump = null;
  formData.value.granularity = null;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
