<template>
  <qc-function-form-template
    function-title="flagIsolated"
    v-model:label="label"
    @submit="submitForm"
    @remove="removeForm"
  >
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

    <!-- gap_window        -->

    <qc-function-form-offset-input
      :rules="[rules.REQUIRED, rules.CONTEXT_WINDOW]"
      class="q-mb-md"
      v-model="formData.gap_window"
      label="gap_window *"
      hint="Minimum gap size required before and after a group to consider it isolated."
    />

    <!-- group_window        -->

    <qc-function-form-offset-input
      :rules="[rules.REQUIRED, rules.CONTEXT_WINDOW]"
      class="q-mb-md"
      v-model="formData.group_window"
      label="group_window *"
      hint="Maximum size of a data chunk to consider for isolation."
    />

    <!-- flag     -->
    <q-input
      class="q-mb-md"
      filled
      :model-value="formData.flag"
      label="Flag (enter a floating point number)"
      :rules="[ruleFactories.MIN(0)]"
      @update:model-value="(val) => (formData.flag = toNumberOrNull(val))"
       hint="Flag assigned to values identified by this function. Defaults to 255 if left empty."
    />

    <!-- dfilter    -->
    <q-input
      class="q-mb-md"
      filled
      :model-value="formData.dfilter"
      :rules="[rules.FLOAT]"
      label="dfilter (enter a floating point number)"
      @update:model-value="(val) => (formData.dfilter = toNumberOrNull(val))"
      hint="Values with flags greater than or equal to this threshold are treated as missing during processing. Defaults to 0 if left empty."
    />
  </qc-function-form-template>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue';
import StaDatastreamInput from '@/components/StaDatastreamInput.vue';
import QcFunctionFormOffsetInput from '@/components/QcFunctionFormOffsetInput.vue';
import type { QualityControlFunctionArgumentBase } from '@/services/quality_control_setting/types';
import QcFunctionFormTemplate from '@/components/QcFunctionFormTemplate.vue';
import { POSSIBLE_QC_FUNCTION_TYPES } from '@/utils/quality_control_utils';
import type { Datastream } from '@/services/sta/types';
import { ruleFactories, rules } from '@/utils/validation/rules';
import { toNumberOrNull, nullableNumber } from '@/utils/quality_control_function_utils';

const props = defineProps<{
  permission_group_id: number;
  initialData?: QualityControlFunctionArgumentBase[];
}>();

const label = defineModel<string | undefined>('label');

const formData = ref({
  field: [] as Datastream[],
  target: [] as Datastream[],
  gap_window: null as number | null,
  group_window: null as number | null,
  flag: nullableNumber(255.0),
  dfilter: nullableNumber(0),
});

function loadInitialData() {
  if (!props.initialData) return;

  const fieldArg = props.initialData.find((a) => a.name === 'field');
  const targetArg = props.initialData.find((a) => a.name === 'target');
  const gap_windowArg = props.initialData.find((a) => a.name === 'gap_window');
  const group_windowArg = props.initialData.find((a) => a.name === 'group_window');
  const flagArg = props.initialData.find((a) => a.name === 'flag');
  const dfilterArg = props.initialData.find((a) => a.name === 'dfilter');

  formData.value.field = (fieldArg?.input.value as Datastream[]) ?? [];
  formData.value.target = (targetArg?.input.value as Datastream[]) ?? [];
  formData.value.gap_window = (gap_windowArg?.input.value as number) ?? null;
  formData.value.group_window = (group_windowArg?.input.value as number) ?? null;
  formData.value.flag = (flagArg?.input.value as number) ?? 255.0;
  formData.value.dfilter = (dfilterArg?.input.value as number) ?? 0;
}
watch(() => props.initialData, loadInitialData, { immediate: true });

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
  const flagObject = {
    name: 'flag',
    input: { value: formData.value.flag ?? 255},
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };
  const dfilterObject = {
    name: 'dfilter',
    input: { value: formData.value.dfilter ?? 0},
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };

  // include required fields
  const returnArray: Array<QualityControlFunctionArgumentBase> = [
    fieldObject,
    gap_windowObject,
    group_windowObject,
    flagObject,
    dfilterObject,
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
  formData.value.flag = 255.0;
  formData.value.dfilter = 0;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
