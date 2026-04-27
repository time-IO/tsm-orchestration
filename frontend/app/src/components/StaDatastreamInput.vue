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
        <q-tooltip v-if="!permission_group_id"> Please select a permission group first </q-tooltip>
      </div>

      <div v-else>
        <div class="row items-start no-wrap">
          <div style="width: 90%">
            <sta-datastream-selection-view
              :selected="selectedDatastreams"
              hide-open-button
              :default-opened="false"
              @remove="removeSelected"
              :style="{ maxHeight: maxHeight || '200px', overflowY: 'auto' }"
            />
          </div>
          <div class="q-ml-sm">
            <q-btn
              flat
              round
              dense
              icon="edit"
              @click="openDialog"
              :disable="!permission_group_id"
            />
            <q-tooltip v-if="!permission_group_id">
              Please select a permission group first
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
    </div>
  </q-field>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Datastream } from 'src/services/sta/types';
import StaDatastreamSelectionView from 'components/StaDatastreamSelectionView.vue';
import StaDatastreamSelection from 'components/StaDatastreamSelection.vue';

const selectedDatastreams = defineModel<Datastream[]>({ default: [] });

const showDialog = ref(false);
const hasSelection = computed(() => selectedDatastreams.value.length > 0);

defineProps<{
  permission_group_id: number;
  maxHeight?: string | number;
  rules?: ((val: Datastream[] | null) => boolean | string)[];
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
</script>

<style scoped></style>
