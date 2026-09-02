<template>
  <qc-function-form-template
    function-title="processGeneric"
    v-model:label="label"
    @submit="submitForm"
    @remove="removeForm"
  >
    <!-- field        -->
    <div class="q-mb-md">
      <span class="text-bold block">Field *</span>
      <span class="text-caption text-grey block q-mb-sm"> Input data stream(s). </span>
      <sta-datastream-input
        max-height="300px"
        :rules="[rules.LIST, ruleFactories.MIN(1)]"
        v-model="formData.field"
        :permission_group_id="permission_group_id"
      />
    </div>

    <!-- target        -->
    <div class="q-mb-md">
      <span class="text-bold block">Target *</span>
      <span class="text-caption text-grey block q-mb-sm">
        Output data stream(s) to which the results are written. Defaults to field if null.
      </span>
      <sta-datastream-input
        max-height="300px"
        :rules="[rules.LIST, ruleFactories.MIN(1)]"
        v-model="formData.target"
        :permission_group_id="permission_group_id"
        :showTempCreateBtn="true"
      />
    </div>

    <!-- function       -->
    <div class="q-mb-md">
      <q-input filled v-model="formData.func" :rules="[rules.REQUIRED]" label="Function *" />
      <span class="text-caption text-grey block">
        Expression or function applied to the selected input fields (e.g. (x + y) / 2). Variables
        are mapped to the selected fields by position, regardless of their names, and are provided
        as pandas.Series. The function must return one pandas.Series for each selected target.
      </span>
    </div>
  </qc-function-form-template>
</template>

<script setup lang="ts">
import QcFunctionFormTemplate from 'components/QcFunctionFormTemplate.vue';
import StaDatastreamInput from 'components/StaDatastreamInput.vue';
import { computed, ref, watch } from 'vue';
import type { QualityControlFunctionArgumentBase } from 'src/services/quality_control_setting/types';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';
import type { Datastream } from 'src/services/sta/types';
import { ruleFactories, rules } from 'src/utils/validation/rules';

const props = defineProps<{
  permission_group_id: number;
  initialData?: QualityControlFunctionArgumentBase[];
}>();

const label = defineModel<string | undefined>('label');
const emit = defineEmits(['submit', 'remove']);

const formData = ref({
  field: [] as Datastream[],
  target: [] as Datastream[],
  func: '' as string,
});

function loadInitialData() {
  if (!props.initialData) return;

  const fieldArg = props.initialData.find((a) => a.name === 'field');
  const targetArg = props.initialData.find((a) => a.name === 'target');
  const funcArg = props.initialData.find((a) => a.name === 'function');

  formData.value.field = (fieldArg?.input.value as Datastream[]) ?? [];
  formData.value.target = (targetArg?.input.value as Datastream[]) ?? [];
  formData.value.func = (funcArg?.input.value as string) ?? '';
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
  const funcObject = {
    name: 'function',
    input: { value: formData.value.func },
    type: POSSIBLE_QC_FUNCTION_TYPES.FUNCTION,
  };

  // include required fields
  const returnArray: Array<QualityControlFunctionArgumentBase> = [
    fieldObject,
    targetObject,
    funcObject,
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
  formData.value.func = '';
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
