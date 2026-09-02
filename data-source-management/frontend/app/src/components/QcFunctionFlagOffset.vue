<template>
  <qc-function-form-template
    function-title="flagJumps"
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

    <!--        tolerance-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.tolerance"
      label="tolerance * (enter a floating point number)"
      :rules="[rules.FLOAT, rules.REQUIRED, ruleFactories.MIN(0)]"
      hint="Maximum allowed difference between preceding and succeeding values."
    />

    <!--        window-->
    <qc-function-form-offset-input
      :rules="[rules.REQUIRED, rules.CONTEXT_WINDOW]"
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
      :rules="[ruleFactories.MIN(0)]"
      hint="Minimum absolute difference to consider a sequence as an offset."
    />

    <!--        thresh_relative-->

    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.thresh_relative"
      label="thresh_relative (enter a floating point number)"
      :rules="[rules.FLOAT]"
      hint="Minimum relative change to consider a sequence as an offset."
    />

    <!-- flag     -->
    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.flag"
      label="Flag"
      :rules="[rules.FLOAT, ruleFactories.MIN(0)]"
      hint="Flag assigned to values identified by this function."
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
import StaDatastreamInput from 'components/StaDatastreamInput.vue';
import { computed, ref, watch } from 'vue';
import QcFunctionFormOffsetInput from 'components/QcFunctionFormOffsetInput.vue';
import type { QualityControlFunctionArgumentBase } from 'src/services/quality_control_setting/types';
import QcFunctionFormTemplate from 'components/QcFunctionFormTemplate.vue';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';
import type { Datastream } from 'src/services/sta/types';
import { ruleFactories, rules } from 'src/utils/validation/rules';

const props = defineProps<{
  permission_group_id: number;
  initialData?: QualityControlFunctionArgumentBase[];
}>();

const formData = ref({
  field: [] as Datastream[],
  target: [] as Datastream[],
  tolerance: null as number | null,
  window: null as number | null,
  thresh: null as number | null,
  thresh_relative: null as number | null,
  flag: 255.0 as number | null,
  dfilter: 0 as number | null,
});

const label = defineModel<string | undefined>('label');

function loadInitialData() {
  if (!props.initialData) return;

  const fieldArg = props.initialData.find((a) => a.name === 'field');
  const targetArg = props.initialData.find((a) => a.name === 'target');
  const toleranceArg = props.initialData.find((a) => a.name === 'tolerance');
  const windowArg = props.initialData.find((a) => a.name === 'window');
  const threshArg = props.initialData.find((a) => a.name === 'thresh');
  const thresh_relativeArg = props.initialData.find((a) => a.name === 'thresh_relative');
  const flagArg = props.initialData.find((a) => a.name === 'flag');
  const dfilterArg = props.initialData.find((a) => a.name === 'dfilter');

  formData.value.field = (fieldArg?.input.value as Datastream[]) ?? [];
  formData.value.target = (targetArg?.input.value as Datastream[]) ?? [];
  formData.value.tolerance = (toleranceArg?.input.value as number) ?? null;
  formData.value.window = (windowArg?.input.value as number) ?? null;
  formData.value.thresh = (threshArg?.input.value as number) ?? null;
  formData.value.thresh_relative = (thresh_relativeArg?.input.value as number) ?? null;
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
    toleranceObject,
    flagObject,
    dfilterObject,
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
  formData.value.flag = 255.0;
  formData.value.dfilter = 0;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
