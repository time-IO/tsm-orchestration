<template>
  <q-dialog v-model="showDialog" @keydown.enter="addTemporaryDatastream">
    <q-card style="min-width: 50vh" class="q-pa-md">
      <q-card-section class="row q-mb-sm" horizontal>
        <div class="text-h6">Create Datastream</div>
        <q-space />
        <q-btn v-close-popup dense flat icon="close" round />
      </q-card-section>
      <div>
        <div class="q-mb-sm">
          <sta-thing-selection v-model="selectedThing" :permission_group_id="permission_group_id" />
        </div>
        <div class="q-mb-sm">
          <q-input
            v-model="datastreamName"
            dense
            outlined
            label="Datastream name"
            :error-message="nameExists ? 'name already exists' : ''"
          />
        </div>
        <div>
          <q-btn
            @click="addTemporaryDatastream"
            color="primary"
            label="Add Datastream"
            :disabled="!canAdd"
          />
        </div>
      </div>
    </q-card>
  </q-dialog>
</template>
<script setup lang="ts">
import StaThingSelection from 'components/StaThingSelection.vue';
import { ref, computed } from 'vue';
import type { StaEntity, Datastream, TemporaryDatastream } from 'src/services/sta/types';

const showDialog = defineModel<boolean>({ default: false });

const { alreadySelectedThing, existingDatastreams } = defineProps<{
  alreadySelectedThing: StaEntity | null;
  existingDatastreams: Datastream[];
  permission_group_id: number;
}>();

const emit = defineEmits<{
  (e: 'add-temporary', ds: TemporaryDatastream): void;
}>();

const selectedThing = ref<StaEntity | null>(alreadySelectedThing);
const datastreamName = ref('');

const nameExists = computed(() => {
  if (!datastreamName.value.trim()) return false;
  return existingDatastreams.some((ds: Datastream) => ds.name === datastreamName.value.trim());
});

const canAdd = computed(
  () => selectedThing.value && datastreamName.value.trim().length > 0 && !nameExists.value,
);

function addTemporaryDatastream() {
  if (!canAdd.value || !selectedThing.value) return;

  const thingId = selectedThing.value['@iot.id'] ?? 'CREATED';

  const temp: TemporaryDatastream = {
    '@iot.id': null,
    '@iot.selfLink': null,
    Thing: selectedThing.value,
    name: datastreamName.value.trim(),
    alias: `T${thingId}S${datastreamName.value.trim()}`,
  };

  emit('add-temporary', temp);
  datastreamName.value = '';
  selectedThing.value = null;
}
</script>

<style scoped></style>
