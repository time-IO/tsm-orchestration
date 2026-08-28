<template>
  <qc-function-form-template function-title="flagZScore" v-model:label="label" @submit="submitForm" @remove="removeForm">
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
      :rules_int="[rules.INTEGER, ruleFactories.MIN(1)]"
      :rules_offset="[rules.CONTEXT_WINDOW]"
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
      :rules="[ruleFactories.MIN(0), rules.FLOAT]"
      hint="Z-score threshold."
    />
    <!--    min_residuals-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.min_residuals"
      label="min_residuals * (enter a floating point number)"
      :rules="[ruleFactories.MIN(0), rules.FLOAT]"
      hint="Minimum residual to consider a point as outlier."
    />
    <!--    min_periods-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.min_periods"
      label="min_periods (enter a integer number)"
      :rules="[rules.INTEGER, ruleFactories.MIN(1)]"
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
      :rules="[rules.INTEGER, ruleFactories.MIN(0), ruleFactories.MAX(1)]"
      hint="Axis along which scoring is applied."
    />

    <!-- flag     -->
    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.flag"
      label="Flag (enter a floating point number)"
      :rules="[ruleFactories.MIN(0), rules.FLOAT]"
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
import type { QualityControlFunctionArgumentBase } from 'src/services/quality_control_setting/types';
import QcFunctionFormIntOffsetInput from 'components/QcFunctionFormIntOffsetInput.vue';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';
import type { Datastream } from 'src/services/sta/types';
import { ruleFactories, rules } from 'src/utils/validation/rules';
import QcFunctionFormTemplate from "components/QcFunctionFormTemplate.vue";

const props = defineProps<{
  permission_group_id: number;
  initialData?: QualityControlFunctionArgumentBase[];
}>();

const label = defineModel<string | undefined>('label');
const emit = defineEmits(['submit', 'remove']);
const current_window_type = ref(POSSIBLE_QC_FUNCTION_TYPES.INT);

const methodOptions: Array<string> = ['standard', 'modified'];

const formData = ref({
  field: [] as Datastream[],
  target: [] as Datastream[],
  method: null as number | null,
  window: null as number | null,
  thresh: null as number | null,
  min_residuals: null as number | null,
  min_periods: null as number | null,
  center: true,
  axis: null as number | null,
  flag: 255.0 as number | null,
  dfilter: 0 as number | null,
});

function loadInitialData() {
  if (!props.initialData) return;

  const fieldArg = props.initialData.find((a) => a.name === 'field');
  const targetArg = props.initialData.find((a) => a.name === 'target');
  const methodArg = props.initialData.find((a) => a.name === 'method');
  const windowArg = props.initialData.find((a) => a.name === 'window');
  const threshArg = props.initialData.find((a) => a.name === 'thresh');
  const min_residualsArg = props.initialData.find((a) => a.name === 'min_residuals');
  const min_periodsArg = props.initialData.find((a) => a.name === 'min_periods');
  const centerArg = props.initialData.find((a) => a.name === 'center');
  const axisArg = props.initialData.find((a) => a.name === 'axis');
  const flagArg = props.initialData.find((a) => a.name === 'flag');
  const dfilterArg = props.initialData.find((a) => a.name === 'dfilter');

  formData.value.field = (fieldArg?.input.value as Datastream[]) ?? [];
  formData.value.target = (targetArg?.input.value as Datastream[]) ?? [];
  formData.value.method = (methodArg?.input.value as number) ?? null;
  formData.value.window = (windowArg?.input.value as number) ?? null;
  formData.value.thresh = (threshArg?.input.value as number) ?? null;
  formData.value.min_residuals = (min_residualsArg?.input.value as number) ?? null;
  formData.value.min_periods = (min_periodsArg?.input.value as number) ?? null;
  formData.value.center = (centerArg?.input.value as boolean) ?? true;
  formData.value.axis = (axisArg?.input.value as number) ?? null;
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
    flagObject,
    dfilterObject,
  ];

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
  formData.value.flag = 255.0;
  formData.value.dfilter = 0;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
