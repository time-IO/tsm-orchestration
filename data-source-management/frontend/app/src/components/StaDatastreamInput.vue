<template>
  <q-field :rules="rules" v-model="selectedDatastreams">
    <div class="q-mb-md full-width">
      <div class="q-mb-sm">
        <q-btn
          :label="hasSelection ? 'Edit Datastreams' : 'Select Datastreams'"
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
        <q-tooltip v-if="!permission_group_id"> Please select a Permission Group first </q-tooltip>
      </div>

      <div v-if="!hasSelection" class="text-grey">No datastreams selected</div>
      <template v-else>
        <sta-thing-datastreams-card
          v-for="group in selectedGroups"
          :key="group.thingName"
          class="q-mb-sm"
          :thing-name="group.thingName"
          :datastreams="group.datastreams"
          :expanded="expandedThings[group.thingName] ?? true"
          @update:expanded="(val: boolean) => (expandedThings[group.thingName] = val)"
          removable
          hide-thing-name
          hide-open-button
          @remove="removeSelected"
        />
      </template>

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
import { computed, reactive, ref } from 'vue';
import type { Datastream, TemporaryDatastream } from '@/services/sta/types';
import StaDatastreamSelection from '@/components/StaDatastreamSelection.vue';
import StaThingDatastreamsCard from '@/components/StaThingDatastreamsCard.vue';
import StaTemporaryDatastreamCreation from '@/components/StaTemporaryDatastreamCreation.vue';
import { groupDatastreamsByThing } from '@/utils/sta_utils';

const selectedDatastreams = defineModel<Datastream[]>({ default: () => [] });

const showDialog = ref(false);
const hasSelection = computed(() => selectedDatastreams.value.length > 0);
const selectedGroups = computed(() => groupDatastreamsByThing(selectedDatastreams.value));
const expandedThings = reactive<Record<string, boolean>>({});

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
