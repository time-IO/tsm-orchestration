<template>
  <qc-function-form-template
    function-title="flagUniLOF"
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

    <!--    n-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.n"
      label="n (enter a integer number)"
      :rules="[rules.INTEGER, ruleFactories.MIN(0)]"
      hint="Number of periods to include in LOF calculation."
    />

    <!--thresh-->
    <qc-function-form-float-enum-input
      class="q-mb-md"
      v-model:input="formData.thresh"
      v-model:current_type="current_thresh_type"
      label="thresh"
      :rules_float="[ruleFactories.MIN(0)]"
      :rules_enum="[]"
      :enum-options="['auto']"
      hint="LOF cutoff value."
    />

    <!--probability-->
    <q-input
      class="q-mb-md"
      filled
      v-model.number="formData.probability"
      label="probability (enter a floating point number)"
      :rules="[ruleFactories.RANGE(0, 1), rules.FLOAT]"
      hint="Outlier probability cutoff."
    />

    <!--corruption-->
    <qc-function-form-float-int-input
      label="corruption"
      class="q-mb-md"
      v-model:input.number="formData.corruption"
      v-model:current_type="current_corruption_type"
      :rules_float="[rules.FLOAT, ruleFactories.RANGE(0, 1)]"
      :rules_int="[rules.INTEGER, ruleFactories.MIN(0)]"
      hint_float="Portion of data considered anomalous."
      hint_int="Count of data considered anomalous."
    />

    <!--algorithm-->
    <q-select
      v-model="formData.algorithm"
      :options="algorithmOptions"
      class="q-mb-md"
      label="algorithm"
      hint="Algorithm for nearest neighbor calculation."
      filled
    />

    <!--p-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.p"
      label="p (enter a integer number)"
      :rules="[rules.INTEGER, ruleFactories.MIN(1)]"
      hint="Minkowski metric degree."
    />

    <!--density-->
    <qc-function-form-float-enum-input
      v-model:input="formData.density"
      v-model:current_type="current_density_type"
      label="density"
      :rules_float="[ruleFactories.MIN(0)]"
      :rules_enum="[]"
      :enum-options="['auto']"
      hint="LOF cutoff value."
    />

    <!--fill_na-->
    <div class="q-mb-md">
      <q-item tag="label" v-ripple>
        <q-item-section avatar>
          <q-toggle v-model="formData.fill_na" />
        </q-item-section>
        <q-item-section>
          <q-item-label>fill_na</q-item-label>
          <q-item-label caption>Fill NaNs via interpolation if True.</q-item-label>
        </q-item-section>
      </q-item>
    </div>

    <!--slope_correct-->
    <div class="q-mb-md">
      <q-item tag="label" v-ripple>
        <q-item-section avatar>
          <q-toggle v-model="formData.slope_correct" />
        </q-item-section>
        <q-item-section>
          <q-item-label>slope_correct</q-item-label>
          <q-item-label caption>Remove clusters caused by steep slopes.</q-item-label>
        </q-item-section>
      </q-item>
    </div>

    <!--min_offset-->
    <q-input
      class="q-mb-md"
      filled
      v-model="formData.min_offset"
      label="min_offset (enter a floating point number)"
      :rules="[ruleFactories.MIN(0), rules.FLOAT]"
      hint="Minimum value jump before and after clusters to flag."
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
import QcFunctionFormTemplate from 'components/QcFunctionFormTemplate.vue';
import StaDatastreamInput from 'components/StaDatastreamInput.vue';
import { computed, ref, watch } from 'vue';
import type { QualityControlFunctionArgumentBase } from 'src/services/quality_control_setting/types';
import { POSSIBLE_QC_FUNCTION_TYPES } from 'src/utils/quality_control_utils';
import QcFunctionFormFloatEnumInput from 'components/QcFunctionFormFloatEnumInput.vue';
import QcFunctionFormFloatIntInput from 'components/QcFunctionFormFloatIntInput.vue';
import type { Datastream } from 'src/services/sta/types';
import { ruleFactories, rules } from 'src/utils/validation/rules';

const props = defineProps<{
  permission_group_id: number;
  initialData?: QualityControlFunctionArgumentBase[];
}>();

const label = defineModel<string | undefined>('label');
const emit = defineEmits(['submit', 'remove']);

const current_thresh_type = ref(POSSIBLE_QC_FUNCTION_TYPES.ENUM);
const current_density_type = ref(POSSIBLE_QC_FUNCTION_TYPES.ENUM);
const current_corruption_type = ref(POSSIBLE_QC_FUNCTION_TYPES.FLOAT);

const algorithmOptions = ['ball_tree', 'kd_tree', 'brute', 'auto'];

const formData = ref({
  field: [] as Datastream[],
  target: [] as Datastream[],
  n: 20 as number,
  thresh: 'auto' as string | number,
  probability: null as number | null,
  corruption: null as number | null,
  algorithm: 'ball_tree',
  p: 1 as number,
  density: 'auto' as string | number,
  fill_na: true,
  slope_correct: true,
  min_offset: null as number | null,
  flag: 255.0 as number | null,
  dfilter: 0 as number | null,
});

function loadInitialData() {
  if (!props.initialData) return;

  const fieldArg = props.initialData.find((a) => a.name === 'field');
  const targetArg = props.initialData.find((a) => a.name === 'target');
  const nArg = props.initialData.find((a) => a.name === 'n');
  const threshArg = props.initialData.find((a) => a.name === 'thresh');
  const probabilityArg = props.initialData.find((a) => a.name === 'probability');
  const corruptionArg = props.initialData.find((a) => a.name === 'corruption');
  const algorithmArg = props.initialData.find((a) => a.name === 'algorithm');
  const pArg = props.initialData.find((a) => a.name === 'p');
  const densityArg = props.initialData.find((a) => a.name === 'density');
  const fillNaArg = props.initialData.find((a) => a.name === 'fill_na');
  const slopeCorrectArg = props.initialData.find((a) => a.name === 'slope_correct');
  const minOffsetArg = props.initialData.find((a) => a.name === 'min_offset');
  const flagArg = props.initialData.find((a) => a.name === 'flag');
  const dfilterArg = props.initialData.find((a) => a.name === 'dfilter');

  formData.value.field = (fieldArg?.input.value as Datastream[]) ?? [];
  formData.value.target = (targetArg?.input.value as Datastream[]) ?? [];
  formData.value.n = (nArg?.input.value as number) ?? 20;
  formData.value.thresh = (threshArg?.input.value as string | number) ?? 'auto';
  formData.value.probability = (probabilityArg?.input.value as number) ?? null;
  formData.value.corruption = (corruptionArg?.input.value as number) ?? null;
  formData.value.algorithm = (algorithmArg?.input.value as string) ?? 'ball_tree';
  formData.value.p = (pArg?.input.value as number) ?? 1;
  formData.value.density = (densityArg?.input.value as string | number) ?? 'auto';
  formData.value.fill_na = (fillNaArg?.input.value as boolean) ?? true;
  formData.value.slope_correct = (slopeCorrectArg?.input.value as boolean) ?? true;
  formData.value.min_offset = (minOffsetArg?.input.value as number) ?? null;
  formData.value.flag = (flagArg?.input.value as number) ?? null;
  formData.value.dfilter = (dfilterArg?.input.value as number) ?? null;

  if (threshArg) {
    current_thresh_type.value = threshArg.type;
  }
  if (corruptionArg) {
    current_corruption_type.value = corruptionArg.type;
  }
  if (densityArg) {
    current_density_type.value = densityArg.type;
  }
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
  const nObject = {
    name: 'n',
    input: { value: formData.value.n },
    type: POSSIBLE_QC_FUNCTION_TYPES.INT,
  };

  const threshObject = {
    name: 'thresh',
    input: { value: formData.value.thresh },
    type: current_thresh_type.value,
  };

  const probabilityObject = {
    name: 'probability',
    input: { value: formData.value.probability },
    type: POSSIBLE_QC_FUNCTION_TYPES.FLOAT,
  };
  const corruptionObject = {
    name: 'corruption',
    input: { value: formData.value.corruption },
    type: current_corruption_type.value,
  };

  const algorithmObject = {
    name: 'algorithm',
    input: { value: formData.value.algorithm },
    type: POSSIBLE_QC_FUNCTION_TYPES.ENUM,
  };

  const pObject = {
    name: 'p',
    input: { value: formData.value.p },
    type: POSSIBLE_QC_FUNCTION_TYPES.INT,
  };

  const densityObject = {
    name: 'density',
    input: { value: formData.value.density },
    type: current_density_type.value,
  };

  const fill_naObject = {
    name: 'fill_na',
    input: { value: formData.value.fill_na },
    type: POSSIBLE_QC_FUNCTION_TYPES.BOOL,
  };

  const slope_correctObject = {
    name: 'slope_correct',
    input: { value: formData.value.slope_correct },
    type: POSSIBLE_QC_FUNCTION_TYPES.BOOL,
  };

  const min_offsetObject = {
    name: 'min_offset',
    input: { value: formData.value.min_offset },
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
    flagObject,
    dfilterObject,
  ];

  // only add optional fields if their value is not null
  if (formData.value.target.length > 0) {
    returnArray.push(targetObject);
  }
  if (formData.value.probability !== null) {
    returnArray.push(probabilityObject);
  }
  if (formData.value.corruption !== null) {
    returnArray.push(corruptionObject);
  }
  if (formData.value.min_offset !== null) {
    returnArray.push(min_offsetObject);
  }
  if (formData.value.n !== null) {
    returnArray.push(nObject);
  }
  if (formData.value.thresh !== null) {
    returnArray.push(threshObject);
  }
  if (formData.value.algorithm !== null) {
    returnArray.push(algorithmObject);
  }
  if (formData.value.p !== null) {
    returnArray.push(pObject);
  }
  if (formData.value.density !== null) {
    returnArray.push(densityObject);
  }
  if (formData.value.fill_na !== null) {
    returnArray.push(fill_naObject);
  }
  if (formData.value.slope_correct !== null) {
    returnArray.push(slope_correctObject);
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
  formData.value.n = 20;
  formData.value.thresh = 'auto';
  formData.value.probability = null;
  formData.value.corruption = null;
  formData.value.algorithm = 'ball_tree';
  formData.value.p = 1;
  formData.value.density = 'auto';
  formData.value.fill_na = true;
  formData.value.slope_correct = true;
  formData.value.min_offset = null;
  formData.value.flag = 255.0;
  formData.value.dfilter = 0;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
