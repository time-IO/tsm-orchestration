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

          <div style="width: 100%; overflow-x: auto">
            <q-virtual-scroll :items="datastreams" virtual-scroll-horizontal>
              <template #default="{ item: ds }">
                <sta-datastream-card
                  :datastream="ds"
                  :removable="removable"
                  :hide-open-button="hideOpenButton"
                  @remove="removeDatastream"
                />
              </template>
            </q-virtual-scroll>
          </div>
        </q-expansion-item>
      </div>
    </template>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue';
import type { Datastream } from 'src/services/sta/types';
import StaDatastreamCard from 'components/StaDatastreamCard.vue';

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
