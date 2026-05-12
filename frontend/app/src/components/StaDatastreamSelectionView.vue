<template>
  <div style="height: 100%; overflow-y: auto">
    <template v-if="selected.length === 0">
      <div class="row justify-center items-center" style="height: 100%">
        <div class="text-h6 text-center">No datastreams selected</div>
      </div>
    </template>

    <template v-else>
      <div v-for="(datastreams, thingName) in groupedByThing" :key="thingName" class="col-12">
        <q-expansion-item
          expand-separator
          dense
          header-class="justify-between q-pl-sm"
          :default-opened="defaultOpened"
        >
          <template #header>
            <div class="row items-center" style="width: 100%">
              <span>{{ thingName }}</span>
              <div class="row items-center">
                <q-chip dense color="primary" text-color="white">{{ datastreams.length }}</q-chip>
              </div>
            </div>
          </template>


                <q-list dense separator bordered class="rounded-borders">
                  <sta-datastream-list
                    v-for="(ds, index) in datastreams"
                    :key="ds['@iot.id'] ?? index"
                    :datastream="ds"
                    :removable="removable"
                    :hide-open-button="hideOpenButton"
                    @remove="removeDatastream"
                  />
                </q-list>

        </q-expansion-item>
      </div>
    </template>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue';
import type { Datastream } from 'src/services/sta/types';
import StaDatastreamList from 'components/StaDatastreamList.vue';

const props = defineProps<{
  selected: Datastream[];
  removable?: boolean;
  hideOpenButton?: boolean;
  defaultOpened?: boolean;
}>();

const emit = defineEmits<{
  (e: 'remove', datastream: Datastream): void;
}>();

const groupedByThing = computed(() => {
  const map: Record<string, Datastream[]> = {};
  props.selected.forEach((ds) => {
    const thingName = ds.Thing?.name || '-';
    if (!map[thingName]) map[thingName] = [];
    map[thingName].push(ds);
  });
  return map;
});

function removeDatastream(ds: Datastream) {
  emit('remove', ds);
}
</script>

<style scoped></style>
