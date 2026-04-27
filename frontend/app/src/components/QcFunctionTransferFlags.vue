<template>
  <qc-function-form-template
    function-title="transferFlags"
    @submit="submitForm"
    @remove="removeForm"
  >
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

    <!--      squeeze -->
    <div class="q-mb-md">
      <q-item tag="label" v-ripple>
        <q-item-section avatar>
          <q-toggle v-model="formData.squeeze" />
        </q-item-section>
        <q-item-section>
          <q-item-label>squeeze</q-item-label>
          <q-item-label caption>Collapse history into one column.</q-item-label>
        </q-item-section>
      </q-item>
    </div>

    <!--      overwrite-->
    <div class="q-mb-md">
      <q-item tag="label" v-ripple>
        <q-item-section avatar>
          <q-toggle v-model="formData.overwrite" />
        </q-item-section>
        <q-item-section>
          <q-item-label>overwrite</q-item-label>
          <q-item-label caption>Overwrite existing flags if True.</q-item-label>
        </q-item-section>
      </q-item>
    </div>
  </qc-function-form-template>
</template>

<script setup lang="ts">
import QcFunctionFormTemplate from 'components/QcFunctionFormTemplate.vue';
import { requiredDatastreamsRule } from 'src/utils/form_utils';
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
  squeeze: false,
  overwrite: false,
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
  const squeezeObject = {
    name: 'squeeze',
    input: { value: formData.value.squeeze },
    type: POSSIBLE_QC_FUNCTION_TYPES.BOOL,
  };
  const overwriteObject = {
    name: 'overwrite',
    input: { value: formData.value.overwrite },
    type: POSSIBLE_QC_FUNCTION_TYPES.BOOL,
  };

  // include required fields
  const returnArray: Array<QualityControlFunctionArgumentBase> = [fieldObject];

  // only add optional fields if their value is not null
  if (formData.value.target.length > 0) {
    returnArray.push(targetObject);
  }
  if (formData.value.squeeze !== null) {
    returnArray.push(squeezeObject);
  }
  if (formData.value.overwrite !== null) {
    returnArray.push(overwriteObject);
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
  formData.value.squeeze = false;
  formData.value.overwrite = false;
};

const removeForm = () => {
  emit('remove');
};
</script>

<style scoped></style>
