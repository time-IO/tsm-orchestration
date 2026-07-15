<template>
  <div style="height: 100%; overflow-y: auto">
    <template v-if="selected.length === 0">
      <div class="row justify-center items-center" style="height: 100%">
        <div class="text-center">No datastreams selected</div>
      </div>
    </template>

    <template v-else>
      <div v-for="(datastreams, thingName) in groupedByThing" :key="thingName" class="col-12">
        <q-expansion-item
          expand-separator
          dense
          header-class="justify-between q-pl-sm"
          :default-opened="defaultOpened"
          @update:model-value="(val) => setExpanded(thingName, val)"
        >
          <template #header>
            <div class="row items-center" style="width: 100%">
              <span class="text-dark">{{ thingName }}</span>
              <div class="row items-center">
                <q-chip
                  dense
                  color="blue-grey-3"
                  text-color="white"
                  v-if="!expandedState[thingName]"
                  >{{ datastreams.length }}</q-chip
                >
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
              :hide-thing-name="hideThingName"
              @remove="removeDatastream"
            />
          </q-list>
        </q-expansion-item>
      </div>
    </template>
  </div>
</template>
<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import type { Datastream } from 'src/services/sta/types';
import StaDatastreamList from 'components/StaDatastreamList.vue';

const props = defineProps<{
  selected: Datastream[];
  removable?: boolean;
  hideOpenButton?: boolean;
  defaultOpened?: boolean;
  hideThingName?: boolean;
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
const expandedState = reactive<Record<string, boolean>>({});

watch(
  groupedByThing,
  (groups) => {
    Object.keys(groups).forEach((name) => {
      if (!(name in expandedState)) {
        expandedState[name] = props.defaultOpened ?? false;
      }
    });
  },
  { immediate: true },
);

function setExpanded(thingName: string, val: boolean) {
  expandedState[thingName] = val;
}

function removeDatastream(ds: Datastream) {
  emit('remove', ds);
}
</script>

<style scoped></style>
