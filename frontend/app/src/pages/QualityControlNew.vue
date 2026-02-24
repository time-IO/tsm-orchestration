<template>
  <q-page class="q-pa-lg">
    <h5>Create a new QaQc Setting</h5>
    <div class="row">
      <div class="col">
        <q-btn class="q-mb-lg" icon="chevron_left" label="back" to="/quality-control"/>
      </div>
    </div>
    <q-stepper ref="stepper" v-model="step" header-nav>
      <q-step :done="step > 1" :name="1" title="Basic Settings">
        <q-form>
          <q-input v-model="name" class="q-mb-md" label="Name" outlined/>
          <q-select
            v-model="permissionGroup"
            :options="permissionGroupOptions"
            class="q-mb-md"
            label="Permission Group *"
            outlined
          />
          <q-input v-model="description" class="q-mb-md" label="Description" outlined/>
        </q-form>
      </q-step>

      <q-step :done="step > 1" :name="2" caption="Choose your functions" title="SaQc Functions">
        <q-form>
          <q-btn class="q-mb-lg" @click="openFunctionsDialog">Add Function</q-btn>
          <component
            :is="currentFormComponent"
            v-if="currentFormComponent"
            @submit="handleFormSubmit"
          />
        </q-form>
        <q-list bordered separator class="rounded-borders">
          <q-expansion-item
            v-for="(item,i) in addedFunctions"
            :key="i"
          >
            <template #header>
              <q-item-section side>
                <q-icon
                  name="delete"
                  color="red"
                  @click.prevent="removeFunction(i)"
                  class="cursor-pointer"
                />
              </q-item-section>
              <q-item-section>
                {{ item.function_name }}
              </q-item-section>
              <q-space></q-space>
            </template>
            <q-list>
              <q-item v-for="(arg,j) in item.function_args" :key="`${i}-${j}`">
                {{ arg.name }}:{{ arg.value }}
              </q-item>
            </q-list>
          </q-expansion-item>
        </q-list>
      </q-step>
      <q-step :done="step > 2" :name="3" caption="Review and submit" title="Review"> todo</q-step>

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
              :label="step === 3 ? 'Finish' : 'Continue'"
              color="primary"
              @click="increaseStep"
            />
          </div>
        </q-stepper-navigation>
      </template>
    </q-stepper>

    <q-dialog
      v-model="functionDialog"
      backdrop-filter="blur(4px) saturate(150%)"
      full-height
      full-width
      persistent
    >
      <q-card>
        <q-card-section class="row">
          <q-space/>
          <div class="text-h6">Choose a quality control function</div>
          <q-space/>
          <q-btn v-close-popup dense flat icon="close" round/>
        </q-card-section>
        <q-separator inset/>
        <div class="q-pa-md row items-start q-gutter-md">
          <q-card v-for="(item, i) in functionOptions" @click="selectFunction(item)" :key="`function-option-${i}`">
            <q-card-section>
              <div class="text-h6">{{ item.label }}</div>
            </q-card-section>
            <q-separator dark inset/>
            <q-card-section> {{ item.description }}</q-card-section>
          </q-card>
        </div>

      </q-card>
    </q-dialog>
  </q-page>
</template>

<script lang="ts" setup>
import {ref, computed} from 'vue';
import DummyTestForm from 'components/DummyTestForm.vue';
import DummyTestForm2 from 'components/DummyTestForm2.vue';

// Type definition for added functions
interface AddedFunction {
  function_name: string;
  function_args: Record<string, unknown>[]; // Adjust type as needed (e.g., [{ name: string; value: unknown }]
}


const step = ref(2);

const name = ref('');
const description = ref('');
const permissionGroup = ref(null);

const functionDialog = ref(false);

const permissionGroupOptions = ['Permission group 1', 'Permission group 2', 'Permission group 3'];

// Explicitly type selectedFunction and addedFunctions
const selectedFunction = ref<string | null>(null);
const addedFunctions = ref<AddedFunction[]>([]);

const functionOptions = [
  {label: 'flagPlateau', id: 1, description: 'lorem Function 1', component: 'Todo'},
  {label: 'Function 2', id: 2, description: 'lorem Function 2', component: 'Todo'},
  {label: 'Function 3', id: 3, description: 'lorem Function 3', component: 'Todo'},
];

const currentFormComponent = computed(() => {
  switch (selectedFunction.value) {
    case 'flagPlateau':
      return DummyTestForm;
    case 'Function 2':
      return DummyTestForm2;
    // case 'functionC': return FunctionCForm;
    default:
      return null;
  }
});

function handleFormSubmit(formData: Record<string, unknown>[]) {
  console.log('Submitted data for', selectedFunction.value, ':', formData);

  if (!selectedFunction.value) return;

  addedFunctions.value.push(
    {
      function_name: selectedFunction.value,
      function_args: formData
    }
  );

  //reset
  selectedFunction.value = null
}

function removeFunction(index: number) {
  addedFunctions.value.splice(index, 1);
}

function openFunctionsDialog() {
  functionDialog.value = true;
}

function selectFunction(item: { label: string }) {
  functionDialog.value = false;
  selectedFunction.value = item.label
}

function increaseStep() {
  if (step.value < 3) {
    step.value += 1;
  }
}

function decreaseStep() {
  if (step.value > 1) {
    step.value -= 1;
  }
}
</script>

<style scoped></style>
