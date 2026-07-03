<template>
  <q-field :rules="rules" v-model="selectedDatastreams">
    <div class="q-mb-md">
      <div v-if="!hasSelection">
        <q-btn
          label="Select Datastreams"
          :disable="!permission_group_id"
          outline
          @click="openDialog"
        />
        <q-btn class="q-ml-sm" outline v-if="showTempCreateBtn" @click="showCreateDialog = true"
          >Create Datastream</q-btn
        >
        <q-tooltip v-if="!permission_group_id"> Please select a Permission Group first </q-tooltip>
      </div>

      <div v-else>
        <div>
          <div class="q-mb-sm">
            <q-btn
              label="Select Datastreams"
              :disable="!permission_group_id"
              outline
              @click="openDialog"
            />
            <q-btn
              label="Create Datastream"
              class="q-ml-sm"
              outline
              v-if="showTempCreateBtn"
              @click="showCreateDialog = true"
            />
          </div>
          <div style="width: 90%">
            <sta-datastream-card
              label="Datastreams"
              :selected="selectedDatastreams"
              :removable="true"
              :addable="false"
              :hide-thing-name="true"
              :hide-open-button="true"
              @remove="removeSelected"
            />
          </div>
          <div class="q-ml-sm">
            <q-tooltip v-if="!permission_group_id">
              Please select a Permission Group first
            </q-tooltip>
          </div>
        </div>
      </div>

      <sta-datastream-selection
        v-if="showDialog"
        v-model="showDialog"
        :initial-selection="selectedDatastreams"
        :permission_group_id="permission_group_id"
        @apply-selection="applySelection"
      />
      <sta-temporary-datastream-creation
        v-model="showCreateDialog"
        :already-selected-thing="null"
        :existing-datastreams="selectedDatastreams"
        @add-temporary="onAddTemporary"
        :permission_group_id="permission_group_id"
      />
    </div>
  </q-field>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Datastream, TemporaryDatastream } from 'src/services/sta/types';
import StaDatastreamSelection from 'components/StaDatastreamSelection.vue';
import StaDatastreamCard from 'components/StaDatastreamCard.vue';
import StaTemporaryDatastreamCreation from 'components/StaTemporaryDatastreamCreation.vue';

const selectedDatastreams = defineModel<Datastream[]>({ default: [] });

const showDialog = ref(false);
const hasSelection = computed(() => selectedDatastreams.value.length > 0);

defineProps<{
  permission_group_id: number;
  maxHeight?: string | number;
  rules?: ((val: Datastream[] | null) => boolean | string)[];
  showTempCreateBtn?: boolean;
}>();

function applySelection(selection: Datastream[]) {
  selectedDatastreams.value = selection;
  showDialog.value = false;
}

function openDialog() {
  showDialog.value = true;
}

function removeSelected(ds: Datastream) {
  selectedDatastreams.value = selectedDatastreams.value.filter((s) => getKey(s) !== getKey(ds));
}

function getKey(ds: Datastream) {
  const id = ds?.['@iot.id'];
  if (id !== undefined && id !== null) return `sta:${id}`;
  const name = ds?.name ?? '';
  const thingName = ds?.Thing?.name ?? '';
  return `tmp:${thingName}::${name}`;
}

// code for extra button to create temp datastreams

const showCreateDialog = ref(false);

function onAddTemporary(ds: TemporaryDatastream) {
  selectedDatastreams.value.push(ds);
  showCreateDialog.value = false;
}
</script>

<style scoped></style>
