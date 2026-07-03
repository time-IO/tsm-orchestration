<template>
  <q-dialog
    v-model="showDialog"
    maximized
    @keydown.esc="showDialog = false"
    @keydown.enter="applySelection"
  >
    <q-card class="q-pa-lg q-ma-md" style="max-width: 95vw; height: 90vh">
      <div class="q-mb-md">
        <div class="text-h5">Select Datastreams</div>
        <div class="text-grey">
          Filter and select Datastreams from SensorThings API or create new ones
        </div>
      </div>

      <div class="row">
        <div class="col-8">
          <div class="row q-mb-sm">
            <div class="col-6">
              <sta-thing-selection
                v-model="filters.thing"
                @update:model-value="debouncedLoadData"
                :permission_group_id="permission_group_id"
              />
            </div>
          </div>
          <div class="row q-mb-md">
            <div class="col">
              <sta-datastream-search-table
                v-model:filter="filters.datastream"
                v-model:paginationSta="paginationSta"
                v-model:selectedSta="selectedSta"
                @onRequest="updatePaginationAndLoadData"
                :rows="staRows"
                :loading="loading"
              />
            </div>
          </div>
        </div>
        <div class="col-4">
          <sta-datastream-card
            label="Datastreams"
            :selected="selected"
            :removable="true"
            :addable="false"
            :hide-thing-name="true"
            :hide-open-button="true"
            @remove="removeDatastreamFromSelection"
          />
        </div>
      </div>
      <div class="q-mt-md row justify-end q-gutter-sm no-wrap action-buttons">
        <q-btn flat label="Cancel" @click="showDialog = false" />
        <q-btn color="primary" label="Apply selection" @click="applySelection" />
      </div>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import StaThingSelection from 'components/StaThingSelection.vue';
import StaDatastreamSearchTable from 'components/StaDatastreamSearchTable.vue';
import { computed, ref, onMounted, watch } from 'vue';
import type {
  QuasarPaginationInterface,
  StaDatastream,
  StaEntity,
  TemporaryDatastream,
} from 'src/services/sta/types';
import { debounce, useQuasar } from 'quasar';
import { useStaStore } from 'stores/staStore';
import StaDatastreamCard from 'components/StaDatastreamCard.vue';
import type { Datastream } from 'src/services/sta/types';

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

onMounted(async () => {
  await loadData();
});

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

<style scoped>
.action-buttons {
  position: sticky;
  bottom: 0;
}
</style>
