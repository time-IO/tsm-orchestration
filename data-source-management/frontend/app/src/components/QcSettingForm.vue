<template>
  <q-page class="q-pa-lg">
    <h5>{{ title }}</h5>
    <div class="row">
      <div class="col">
        <q-btn class="q-mb-lg" icon="chevron_left" label="back" :to="backUrl"/>
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
            hint="Enter a descriptive name for this QC Setting"
            :rules="[rules.REQUIRED, ruleFactories.MAX(80)]"
          />
          <!-- Permission Group Field -->
          <permission-group-select
            v-model="formData.permission_group_id"
            :preselected-item="itemPermissionGroup"
            :rules="[rules.REQUIRED]"
            class="q-mb-md"
          />
          <!-- Context Window -->
          <q-input
            filled
            class="q-mb-md"
            v-model="formData.context_window"
            label="Context Window *"
            hint="Enter a Context Window for this QC Setting"
            :rules="[rules.REQUIRED, rules.CONTEXT_WINDOW]"
          >
            <template v-slot:append>
              <q-btn round flat icon="help_outline" @click="showContextDocumentation">
                <q-tooltip>View Pandas Docs for information on available aliases</q-tooltip>
              </q-btn>
            </template>
          </q-input>
          <!-- Description -->
          <q-input
            filled
            v-model="formData.description"
            label="Description"
            type="textarea"
            rows="3"
            hint="Provide additional details about this QC Setting"
          />

          <q-card-section class="q-pa-none q-mt-md">
            <div class="text-h6 q-mb-md">Activation Settings</div>

            <q-toggle
              v-model="formData.is_active"
              label="Enable Quality Control"
              color="primary"
              size="md"
            />
          </q-card-section>
        </q-form>
      </q-step>

      <q-step
        :done="step > 1"
        :name="2"
        :disable="!formData.permission_group_id"
        caption="Choose your functions"
        title="SaQC Functions"
      >
        <div class="row justify-end q-mb-lg">
          <q-btn @click="openFunctionsDialog">Add Function</q-btn>
        </div>

        <div class="row">
          <div class="col-12">
            <div class="row items-center justify-end q-mb-sm">
              <q-btn
                flat
                dense
                size="sm"
                :icon="expandAllFunctions ? 'unfold_less' : 'unfold_more'"
                :label="expandAllFunctions ? 'collapse all' : 'expand all'"
                @click="expandAllFunctions = !expandAllFunctions"
                class="text-grey-7"
              />
            </div>
            <qc-function-arg-list-view
              :removable="true"
              :quality_control_functions="formData.quality_control_functions!"
              :expand-all="expandAllFunctions"
              @remove="removeFunction"
              @remove-datastream="handleRemoveDatastream"
              @add-datastream="handleAddDatastream"
              @edit="handleEditFunction"
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
            <q-space/>
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
                !formData.permission_group_id ||
                formData.quality_control_functions!.length == 0 ||
                selectedFunctionName !== null ||
                !hasValidDatastreams
              "
            />
          </div>
        </q-stepper-navigation>
      </template>
    </q-stepper>

    <qc-setting-function-selection-dialog v-model="functionDialog" @select="selectFunction"/>

    <q-dialog v-model="submitDialog">
      <q-card class="full-width">
        <q-card-section>
          <div class="text-h6">Submit Quality Control Settings</div>
        </q-card-section>

        <q-card-section> Are you sure you want to submit?</q-card-section>

        <q-separator/>

        <q-card-actions>
          <q-btn flat @click="closeSubmitDialog()">Cancel</q-btn>
          <q-space></q-space>
          <q-btn flat color="primary" @click="emitSaveAndCloseDialog">Submit</q-btn>
        </q-card-actions>
      </q-card>
    </q-dialog>

    <sta-datastream-selection-dialog
      v-if="formData.permission_group_id"
      v-model="addDatastreamDialog"
      :permission_group_id="formData.permission_group_id!"
      :initial-selection="currentArgSelection"
      @apply-selection="handleApplyDatastreamSelection"
    />

    <q-dialog v-model="functionFormDialog" @hide="handleRemove" no-backdrop-dismiss>
      <q-card style="min-width: 50vw; max-width: 100vw">
        <q-form>
          <component
            :is="currentFunctionFormComponent"
            v-if="currentFunctionFormComponent && formData.permission_group_id"
            :permission_group_id="formData.permission_group_id"
            :initial-data="editingFunction?.quality_control_function_arguments"
            v-model:label="functionLabel"
            @submit="handleFunctionFormSubmit"
            @remove="handleRemove"
          />
        </q-form>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import PermissionGroupSelect from 'components/PermissionGroupSelect.vue';
import {QForm} from 'quasar';
import QcFunctionArgListView from 'components/QcFunctionArgListView.vue';
import QcSettingFunctionSelectionDialog from 'components/QcSettingFunctionSelectionDialog.vue';
import StaDatastreamSelectionDialog from 'components/StaDatastreamSelection.vue';
import {computed, type Ref, ref} from 'vue';
import type {
  QualityControlFunctionCreate,
  QualityControlFunctionArgumentCreate,
  QualityControlSettingCreate,
  QualityControlSettingUpdate,
} from 'src/services/quality_control_setting/types';
import type {FunctionOption} from 'src/utils/quality_control_utils';
import {
  getQcFunctionComponent,
  type QcFunctionName,
} from 'src/utils/quality_control_function_utils';
import type {PermissionGroup} from 'src/services/permission_group/types';
import type {Datastream} from 'src/services/sta/types';
import {isDatastreamType, showContextDocumentation} from 'src/utils/quality_control_utils';
import {FUNCTIONS_WITH_REQUIRED_TARGET} from 'src/utils/quality_control_utils';
import {ruleFactories, rules} from 'src/utils/validation/rules';

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

const functionLabel = ref<string | undefined>(undefined);

const step = ref(1);
const functionDialog = ref(false);
const submitDialog = ref(false);
const qcBaseForm = ref() as Ref<QForm>;
const selectedFunctionName = ref<string | null>(null);
const addDatastreamDialog = ref(false);
const addDatastreamFuncIndex = ref<number>(0);
const addDatastreamArgIndex = ref<number>(0);

const editingIndex = ref<number | null>(null);
const functionFormDialog = ref(false);

const editingFunction = computed(() => {
  if (editingIndex.value === null) return null;
  return formData.value.quality_control_functions![editingIndex.value];
});

const currentFunctionFormComponent = computed(() => {
  if (selectedFunctionName.value) {
    return getQcFunctionComponent(selectedFunctionName.value as QcFunctionName);
  }
  return null;
});

function handleEditFunction(index: number) {
  const func = formData.value.quality_control_functions![index];
  if (!func) return;
  editingIndex.value = index;
  selectedFunctionName.value = func.name;
  functionLabel.value = func.label ?? undefined;
  functionFormDialog.value = true;
}

const currentArgSelection = computed(() => {
  const functions = formData.value.quality_control_functions as QualityControlFunctionCreate[];
  const func = functions[addDatastreamFuncIndex.value];
  if (!func) return [];
  const arg = func.quality_control_function_arguments[addDatastreamArgIndex.value];
  if (!arg) return [];
  return arg.input.value as Datastream[];
});

const hasValidDatastreams = computed(() => {
  return formData.value.quality_control_functions!.every((func) => {
    const field = func.quality_control_function_arguments.find(
      (a) => isDatastreamType(a) && a.name === 'field',
    );
    const target = func.quality_control_function_arguments.find(
      (a) => isDatastreamType(a) && a.name === 'target',
    );
    const targetRequired = FUNCTIONS_WITH_REQUIRED_TARGET.includes(func.name);
    const targetOk = targetRequired
      ? !!target && (target.input.value as Datastream[]).length > 0
      : true;

    const fieldOk = field ? (field.input.value as Datastream[]).length > 0 : true;
    return fieldOk && targetOk;
  });
});

const expandAllFunctions = ref(false);

function handleAddDatastream({funcIndex, argIndex}: { funcIndex: number; argIndex: number }) {
  addDatastreamFuncIndex.value = funcIndex;
  addDatastreamArgIndex.value = argIndex;
  addDatastreamDialog.value = true;
}

function handleApplyDatastreamSelection(selection: Datastream[]) {
  const functions = formData.value.quality_control_functions as QualityControlFunctionCreate[];
  const func = functions[addDatastreamFuncIndex.value];
  if (!func) return;
  const arg = func.quality_control_function_arguments[addDatastreamArgIndex.value];
  if (!arg) return;
  arg.input.value = selection;
  addDatastreamDialog.value = false;
}

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
      .catch(() => {
      });
  }
}

function handleFunctionFormSubmit(submittedData: QualityControlFunctionArgumentCreate[]) {
  if (!selectedFunctionName.value) return;

  if (editingIndex.value !== null) {
    // Edit mode: replace existing function
    formData.value.quality_control_functions![editingIndex.value] = {
      name: selectedFunctionName.value,
      label: functionLabel.value,
      quality_control_function_arguments: submittedData,
    };
    editingIndex.value = null;
  } else {
    // Add mode: attach new function
    formData.value.quality_control_functions!.push({
      name: selectedFunctionName.value,
      label: functionLabel.value,
      quality_control_function_arguments: submittedData,
    });
  }
  selectedFunctionName.value = null;
  functionLabel.value = undefined;
  functionFormDialog.value = false;
}

function removeDatastream(funcIndex: number, argIndex: number, datastream: Datastream) {
  const functions = formData.value.quality_control_functions as QualityControlFunctionCreate[];
  const func = functions[funcIndex];
  if (!func) return;
  const args = func.quality_control_function_arguments;
  const arg = args[argIndex];
  if (!arg) return;
  (arg.input.value as Datastream[]) = (arg.input.value as Datastream[]).filter((ds) =>
    ds['@iot.id'] !== null
      ? ds['@iot.id'] !== datastream['@iot.id']
      : ds.name !== datastream.name || ds.Thing?.name !== datastream.Thing?.name,
  );
}

function handleRemoveDatastream({
                                  funcIndex,
                                  argIndex,
                                  datastream,
                                }: {
  funcIndex: number;
  argIndex: number;
  datastream: Datastream;
}) {
  removeDatastream(funcIndex, argIndex, datastream);
  //reset
}

function selectFunction(item: FunctionOption) {
  functionDialog.value = false;
  selectedFunctionName.value = item.label;
  functionLabel.value = undefined;
  functionFormDialog.value = true;
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
  selectedFunctionName.value = null;
  editingIndex.value = null;
  functionFormDialog.value = false;
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
