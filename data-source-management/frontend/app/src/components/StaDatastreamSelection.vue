<template>
  <q-dialog
    v-model="showDialog"
    maximized
    @keydown.esc="showDialog = false"
    @keydown.enter="applySelection"
  >
    <q-card class="q-pa-lg q-ma-md column no-wrap" style="max-width: 95vw; height: 90vh">
      <div class="q-mb-md">
        <div class="text-h5">Select Datastreams</div>
        <div class="text-grey">
          Filter and select Datastreams from SensorThings API or create new ones
        </div>
      </div>

      <div class="col row no-wrap" style="min-height: 0">
        <div class="col-8 q-pr-xl column no-wrap" style="min-height: 0; min-width: 0">
          <sta-datastream-search-table
            v-model:filter="filters.datastream"
            v-model:paginationSta="paginationSta"
            v-model:selectedSta="selectedSta"
            @onRequest="updatePaginationAndLoadData"
            :rows="staRows"
            :loading="loading"
          >
            <template #filters>
              <sta-thing-selection
                v-model="filters.thing"
                @update:model-value="debouncedLoadData"
                :permission_group_id="permission_group_id"
                style="width: 280px"
              />
            </template>
          </sta-datastream-search-table>
        </div>

        <div class="col-4 column no-wrap" style="min-height: 0">
          <div class="row items-center q-mb-sm" style="min-height: 40px">
            <div class="text-subtitle1 text-weight-medium text-grey-9">Selected Datastreams</div>
            <q-chip v-if="selected.length" dense color="blue-grey-3" text-color="white">
              {{ selected.length }}
            </q-chip>
          </div>

          <div
            v-if="selected.length === 0"
            class="col column flex-center text-center text-grey-5 rounded-borders"
          >
            <q-icon name="playlist_add" size="64px" class="q-mb-md" />
            <div class="text-h5">Selected datastreams will appear here</div>
          </div>

          <q-virtual-scroll
            v-else
            :items="selectedGroups"
            v-slot="{ item }"
            class="col"
            style="min-height: 0"
          >
            <sta-thing-datastreams-card
              :key="item.thingName"
              class="q-mb-sm"
              :thing-name="item.thingName"
              :datastreams="item.datastreams"
              :expanded="expandedThings[item.thingName] ?? true"
              @update:expanded="(val: boolean) => (expandedThings[item.thingName] = val)"
              removable
              hide-thing-name
              hide-open-button
              @remove="removeDatastreamFromSelection"
            />
          </q-virtual-scroll>
        </div>
      </div>

      <div class="q-mt-md row justify-end q-gutter-sm no-wrap">
        <q-btn flat label="Cancel" @click="showDialog = false" />
        <q-btn color="primary" label="Apply selection" @click="applySelection" />
      </div>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import StaThingSelection from '@/components/StaThingSelection.vue';
import StaDatastreamSearchTable from '@/components/StaDatastreamSearchTable.vue';
import { computed, reactive, ref, watch } from 'vue';
import type {
  QuasarPaginationInterface,
  StaDatastream,
  StaEntity,
  TemporaryDatastream,
} from '@/services/sta/types';
import { debounce, useQuasar } from 'quasar';
import { useStaStore } from '@/stores/staStore';
import StaThingDatastreamsCard from '@/components/StaThingDatastreamsCard.vue';
import { groupDatastreamsByThing } from '@/utils/sta_utils';
import type { Datastream } from '@/services/sta/types';

import type { AxiosError } from 'axios';

const staStore = useStaStore();
const $q = useQuasar();

const staRows = ref<StaDatastream[]>([]);

const selectedSta = ref<StaDatastream[]>([]);
const selectedCreated = ref<TemporaryDatastream[]>([]);

const showDialog = defineModel<boolean>({ default: false });
const loading = ref(false);

const props = defineProps<{
  permission_group_id: number;
  initialSelection?: Datastream[];
  removable?: boolean;
}>();

const emit = defineEmits<{
  (e: 'apply-selection', selection: Datastream[]): void;
}>();

const filters = ref<{ datastream: string; thing: StaEntity | null }>({
  datastream: '',
  thing: null,
});

const paginationSta = ref<QuasarPaginationInterface>({
  sortBy: '@iot.id',
  descending: false,
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0,
  pages: 0,
});

const selectedStaWithAlias = computed(() => {
  return selectedSta.value.map((entry) => {
    const thingId = entry.Thing?.['@iot.id'];
    const dsId = entry['@iot.id'];
    entry['alias'] = thingId ? `T${thingId}S${dsId}` : `S${dsId}`;
    return entry;
  });
});
const selectedCreatedWithAlias = computed(() => {
  return selectedCreated.value.map((entry) => {
    const thingId = entry.Thing?.['@iot.id'] ?? 'CREATED';
    entry['alias'] = `T${thingId}S${entry.name}`;
    return entry;
  });
});

const selected = computed(() => [...selectedStaWithAlias.value, ...selectedCreatedWithAlias.value]);

const selectedGroups = computed(() => groupDatastreamsByThing(selected.value));
const expandedThings = reactive<Record<string, boolean>>({});

async function loadData() {
  loading.value = true;

  const requestParams = {
    pagination: paginationSta.value,
    filters: {
      datastream: filters.value.datastream,
      thing: filters.value.thing || null,
    },
  };

  try {
    const response = await staStore.dispatchFetchDatastreams(
      props.permission_group_id,
      requestParams,
    );
    staRows.value = response.value;

    const total = response['@iot.count'] ?? response.value.length;

    paginationSta.value.rowsNumber = total;
    paginationSta.value.pages = Math.ceil(total / paginationSta.value.rowsPerPage);
  } catch (e) {
    const error = e as AxiosError;
    if (error.response?.status === 404) {
      $q.notify({
        type: 'warning',
        position: 'top',
        timeout: 0,
        actions: [
          {
            icon: 'close',
            color: 'black',
            round: true,
            handler: () => {},
          },
        ],
        message:
          'There is no corresponding sta endpoint for your selected permission group. Please change the permission group.',
      });
    }
  } finally {
    loading.value = false;
  }
}
function updatePaginationAndLoadData(pagination: QuasarPaginationInterface) {
  paginationSta.value.rowsPerPage = pagination.rowsPerPage;
  paginationSta.value.page = pagination.page;

  if (pagination.descending) {
    paginationSta.value.descending = pagination.descending;
  }

  if (pagination.sortBy) {
    paginationSta.value.sortBy = pagination.sortBy;
  }

  debouncedLoadData();
}

const debouncedLoadData = debounce(loadData, 400);

function removeDatastreamFromSelection(ds: Datastream) {
  selectedSta.value = selectedSta.value.filter(
    (s: StaDatastream) => s['@iot.id'] !== ds['@iot.id'],
  );
  selectedCreated.value = selectedCreated.value.filter(
    (s: TemporaryDatastream) => s.name !== ds.name || s.Thing?.name !== ds.Thing?.name,
  );
}

function applySelection() {
  emit('apply-selection', selected.value);
}

watch(
  () => props.initialSelection,
  (newSelection) => {
    if (newSelection && Array.isArray(newSelection)) {
      const sta = newSelection.filter((d): d is StaDatastream => d['@iot.id'] !== null);
      const tmp = newSelection.filter((d): d is TemporaryDatastream => d['@iot.id'] === null);
      selectedSta.value = sta;
      selectedCreated.value = tmp;
    }
  },
  { immediate: true },
);
</script>
