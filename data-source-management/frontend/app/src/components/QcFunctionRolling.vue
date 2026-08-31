<template>
  <qc-function-form-template
    function-title="rolling"
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
      <span class="text-bold block">Target</span>
      <span class="text-caption text-grey block q-mb-sm">
        Output data stream(s) to which the results are written. Defaults to field if null.
      </span>
      <sta-datastream-input
        max-height="300px"
        v-model="formData.target"
        :permission_group_id="permission_group_id"
        :showTempCreateBtn="true"
      />
    </div>

    <!--    window-->
    <qc-function-form-offset-input
      :rules="[rules.REQUIRED, rules.CONTEXT_WINDOW]"
      class="q-mb-md"
      v-model="formData.window"
      label="window *"
      hint="Size of the rolling window."
    />
    <!--    func-->

    <q-select
      v-model="formData.func"
      :options="funcOptions"
      class="q-mb-md"
      label="func"
      hint="Function to apply over the rolling window."
      :rules="[rules.REQUIRED]"
      filled
    />
    <!--    min_periods-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.min_periods"
      label="min_periods (enter a integer number)"
      :rules="[rules.INTEGER, ruleFactories.MIN(0)]"
      hint="Minimum points required for a valid result."
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
import QcFunctionFormTemplate from 'components/QcFunctionFormTemplate.vue';
import StaDatastreamInput from 'components/StaDatastreamInput.vue';
import { computed, ref, watch } from 'vue';
import type { QualityControlFunctionArgumentBase } from 'src/services/quality_control_setting/types';
import QcFunctionFormOffsetInput from 'components/QcFunctionFormOffsetInput.vue';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';
import type { Datastream } from 'src/services/sta/types';
import { ruleFactories, rules } from 'src/utils/validation/rules';

const props = defineProps<{
  permission_group_id: number;
  initialData?: QualityControlFunctionArgumentBase[];
}>();

const label = defineModel<string | undefined>('label');
const emit = defineEmits(['submit', 'remove']);

const funcOptions: Array<string> = [
  'sum',
  'mean',
  'median',
  'min',
  'max',
  'std',
  'var',
  'skew',
  'kurt',
];

const formData = ref({
  field: [] as Datastream[],
  target: [] as Datastream[],
  window: null as number | null,
  func: 'mean',
  min_periods: null as number | null,
  center: true,
  flag: 255.0 as number | null,
  dfilter: 0 as number | null,
});

function loadInitialData() {
  if (!props.initialData) return;

  const fieldArg = props.initialData.find((a) => a.name === 'field');
  const targetArg = props.initialData.find((a) => a.name === 'target');
  const windowArg = props.initialData.find((a) => a.name === 'window');
  const funcArg = props.initialData.find((a) => a.name === 'func');
  const min_periodsArg = props.initialData.find((a) => a.name === 'min_periods');
  const centerArg = props.initialData.find((a) => a.name === 'center');
  const flagArg = props.initialData.find((a) => a.name === 'flag');
  const dfilterArg = props.initialData.find((a) => a.name === 'dfilter');

  formData.value.field = (fieldArg?.input.value as Datastream[]) ?? [];
  formData.value.target = (targetArg?.input.value as Datastream[]) ?? [];
  formData.value.window = (windowArg?.input.value as number) ?? null;
  formData.value.func = (funcArg?.input.value as string) ?? 'mean';
  formData.value.min_periods = (min_periodsArg?.input.value as number) ?? null;
  formData.value.center = (centerArg?.input.value as boolean) ?? true;
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
  const windowObject = {
    name: 'window',
    input: { value: formData.value.window },
    type: POSSIBLE_QC_FUNCTION_TYPES.OFFSET,
  };
  const funcObject = {
    name: 'func',
    input: { value: formData.value.func },
    type: POSSIBLE_QC_FUNCTION_TYPES.ENUM,
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
    funcObject,
    flagObject,
    dfilterObject,
  ];

  // only add optional fields if their value is not null
  if (formData.value.target.length > 0) {
    returnArray.push(targetObject);
  }
  if (formData.value.min_periods !== null) {
    returnArray.push(min_periodsObject);
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
  formData.value.window = null;
  formData.value.func = 'mean';
  formData.value.min_periods = null;
  formData.value.center = true;
  formData.value.flag = 255.0;
  formData.value.dfilter = 0;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
