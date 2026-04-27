<template>
  <q-page class="q-pa-lg">
    <h5>{{ title }}</h5>
    <div class="row">
      <div class="col">
        <q-btn class="q-mb-lg" icon="chevron_left" label="back" :to="backUrl" />
      </div>
    </div>
    <q-stepper ref="stepper" v-model="step" header-nav>
      <q-step :done="step > 1" :name="1" title="Basic Settings">
        <q-form ref="qcBaseForm">
          <!-- Name Field -->
          <q-input
            filled
            class="q-mb-md"
            v-model="formData.name"
            label="Name *"
            hint="Enter a descriptive name for this ingest"
            :rules="[(val) => !!val || 'Name is required']"
          />
          <!-- Permission Group Field -->
          <permission-group-select
            v-model="formData.permission_group_id"
            :preselected-item="itemPermissionGroup"
            :rules="[(val) => !!val || 'Permission group is required']"
            class="q-mb-md"
          />
          <!-- Name Field -->
          <q-input
            filled
            class="q-mb-md"
            v-model="formData.context_window"
            label="Context Window *"
            hint="Enter a Context Window for this ingest"
            :rules="[(val) => !!val || 'Context Window is required']"
          />
          <!-- Description -->
          <q-input
            filled
            v-model="formData.description"
            label="Description"
            type="textarea"
            rows="3"
            hint="Provide additional details about this ingest configuration"
          />
        </q-form>
      </q-step>

      <q-step
        :done="step > 1"
        :name="2"
        :disable="!formData.permission_group_id"
        caption="Choose your functions"
        title="SaQC Functions"
      >
        <q-form>
          <q-btn class="q-mb-lg" @click="openFunctionsDialog">Add Function</q-btn>
          <component
            :is="currentFunctionFormComponent"
            v-if="currentFunctionFormComponent && formData.permission_group_id"
            :permission_group_id="formData.permission_group_id"
            @submit="handleFunctionFormSubmit"
            @remove="handleRemove"
          />
        </q-form>
        <div class="row">
          <div class="col-12">
            <qc-function-arg-list-view
              removable
              :quality_control_functions="formData.quality_control_functions!"
              @remove="removeFunction"
            />
          </div>
        </div>
      </q-step>

      <template v-slot:navigation>
        <q-stepper-navigation>
          <div class="row">
            <q-btn
              v-if="step > 1"
              class="q-ml-sm"
              color="primary"
              flat
              label="Back"
              @click="decreaseStep"
            />
            <q-space />
            <q-btn
              v-if="step < 2"
              label="Continue"
              color="primary"
              @click="validateBaseFormAndGoToNextStep"
            />
            <q-btn
              v-else
              label="Submit"
              color="primary"
              @click="openSubmitDialog"
              :loading="isLoading"
              :disable="
                !formData.permission_group_id || formData.quality_control_functions!.length == 0 || selectedFunctionName !== null
              "
            />
          </div>
        </q-stepper-navigation>
      </template>
    </q-stepper>

    <qc-setting-function-selection-dialog v-model="functionDialog" @select="selectFunction" />

    <q-dialog v-model="submitDialog">
      <q-card class="full-width">
        <q-card-section>
          <div class="text-h6">Submit Quality Control Settings</div>
        </q-card-section>

        <q-card-section> Are you sure you want to submit? </q-card-section>

        <q-separator />

        <q-card-actions>
          <q-btn flat @click="closeSubmitDialog()">Cancel</q-btn>
          <q-space></q-space>
          <q-btn flat color="primary" @click="emitSaveAndCloseDialog">Submit</q-btn>
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import { QForm } from 'quasar';
import QcFunctionArgListView from 'components/QcFunctionArgListView.vue';
import QcSettingFunctionSelectionDialog from 'components/QcSettingFunctionSelectionDialog.vue';
import { computed, type Ref, ref } from 'vue';
import type {
  QualityControlFunctionArgumentCreate,
  QualityControlSettingCreate,
  QualityControlSettingUpdate,
} from 'src/services/quality_control_setting/types';
import type { FunctionOption } from 'src/utils/quality_control_utils';
import {
  getQcFunctionComponent,
  type QcFunctionName,
} from 'src/utils/quality_control_function_utils';
import type { PermissionGroup } from 'src/services/permission_group/types';

const formData = defineModel<QualityControlSettingCreate | QualityControlSettingUpdate>({
  default: {
    name: null,
    context_window: null,
    is_active: true,
    description: null,
    permission_group_id: null,
    quality_control_functions: [],
  },
});

defineProps<{
  isLoading: boolean;
  title: string;
  backUrl: string;
  itemPermissionGroup?: PermissionGroup | null;
}>();

const emit = defineEmits(['save']);

const step = ref(1);
const functionDialog = ref(false);
const submitDialog = ref(false);
const qcBaseForm = ref() as Ref<QForm>;
const selectedFunctionName = ref<string | null>(null);

const currentFunctionFormComponent = computed(() => {
  if (selectedFunctionName.value) {
    return getQcFunctionComponent(selectedFunctionName.value as QcFunctionName);
  }
  return null;
});

function validateBaseFormAndGoToNextStep() {
  if (qcBaseForm.value !== null) {
    qcBaseForm.value
      .validate()
      .then((success: boolean) => {
        if (success) {
          step.value += 1;
        } else {
          // oh no, user has filled in
          // at least one invalid value
        }
      })
      .catch(() => {});
  }
}

function handleFunctionFormSubmit(submittedData: QualityControlFunctionArgumentCreate[]) {
  if (!selectedFunctionName.value) return;

  formData.value.quality_control_functions!.push({
    name: selectedFunctionName.value,
    quality_control_function_arguments: submittedData,
  });

  //reset
  selectedFunctionName.value = null;
}

function selectFunction(item: FunctionOption) {
  functionDialog.value = false;
  selectedFunctionName.value = item.label;
}

function openSubmitDialog() {
  submitDialog.value = true;
}

function closeSubmitDialog() {
  submitDialog.value = false;
}

function decreaseStep() {
  if (step.value > 1) {
    step.value -= 1;
  }
}

function handleRemove() {
  //reset
  selectedFunctionName.value = null;
}

function removeFunction(index: number) {
  formData.value.quality_control_functions!.splice(index, 1);
}

function openFunctionsDialog() {
  functionDialog.value = true;
}

function emitSaveAndCloseDialog() {
  emit('save');
  closeSubmitDialog();
}
</script>

<style scoped></style>
