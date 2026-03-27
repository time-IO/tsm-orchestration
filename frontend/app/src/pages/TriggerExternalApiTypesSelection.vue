<template>
  <q-page class="q-pa-lg">
    <h5>{{ metaProvider.title }}</h5>
    <div class="q-mb-md">
      <q-table
        flat
        bordered
        :rows="rows"
        :columns="columns"
        :row-key="(row) => `${row.provider}:${row.id}`"
        :selected-rows-label="getSelectedString"
        selection="multiple"
        v-model:pagination="pagination"
        v-model:selected="selected"
      />
    </div>

    <div class="row q-mb-lg">
      <q-btn icon="chevron_left" label="back" @click="goBack" />
      <q-space />
      <q-btn color="primary" label="Trigger" padding="xs md" @click="goToTriggerPage" />
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import type { QTableColumn } from 'quasar';
import { onMounted, computed, ref } from 'vue';
import type { StoreGeneric } from 'pinia';
import { storeToRefs } from 'pinia';
import { useIngestExternalApiUbaStore } from 'stores/ingestExternalApiUbaStore';
import { useIngestExternalApiNeutronMonitorStore } from 'stores/ingestExternalApiNeutronMonitorStore';
import { useIngestExternalApiDwdStore } from 'stores/ingestExternalApiDwdStore';
import { useIngestExternalApiBoschStore } from 'stores/ingestExternalApiBoschStore';
import { useIngestExternalApiTheThingsNetworkStore } from 'stores/ingestExternalApiTheThingsNetworkStore';
import { useIngestExternalApiTSystemsStore } from 'stores/ingestExternalApiTSystemsStore';
import { useIngestTriggerSelectionStore } from 'stores/triggerExternalApiSelectedStore';

const route = useRoute();
const router = useRouter();
const pagination = ref({
  page: 1,
  rowsPerPage: 25, // 👈 DEFAULT (z. B. 25, 50, 100)
});
const provider = route.query.provider as string;
const triggerSelectionStore = useIngestTriggerSelectionStore();
const { selected } = storeToRefs(triggerSelectionStore);

function getSelectedString() {
  return selected.value.length === 0
    ? ''
    : `${selected.value.length} record${selected.value.length > 1 ? 's' : ''} selected`;
}

async function goToTriggerPage() {
  await router.push({ name: 'triggerSelected' });
}

const stores: Record<string, StoreGeneric> = {
  ingestExternalApiBoschStore: useIngestExternalApiBoschStore(),
  ingestExternalApiDwdStore: useIngestExternalApiDwdStore(),
  ingestExternalApiNeutronMonitorStore: useIngestExternalApiNeutronMonitorStore(),
  ingestExternalApiTheThingsNetworkStore: useIngestExternalApiTheThingsNetworkStore(),
  ingestExternalApiTSystemsStore: useIngestExternalApiTSystemsStore(),
  ingestExternalApiUbaStore: useIngestExternalApiUbaStore(),
};
const providerMetaMap: Record<string, { title: string; store: string; list: string }> = {
  bosch: {
    title: 'Ingest - External Api - Bosch IoT',
    store: 'ingestExternalApiBoschStore',
    list: 'ingestExternalApiBoschList',
  },
  dwd: {
    title: 'Ingest - External Api - DWD',
    store: 'ingestExternalApiDwdStore',
    list: 'ingestExternalApiDwdList',
  },
  'neutron-monitor': {
    title: 'Ingest - External Api - Neutron Monitor',
    store: 'ingestExternalApiNeutronMonitorStore',
    list: 'ingestExternalApiNeutronMonitorList',
  },
  'the-things-network': {
    title: 'Ingest - External Api - The Things Network',
    store: 'ingestExternalApiTheThingsNetworkStore',
    list: 'ingestExternalApiTheThingsNetworkList',
  },
  tsystems: {
    title: 'Ingest - External Api - T-Systems',
    store: 'ingestExternalApiTSystemsStore',
    list: 'ingestExternalApiTSystemsList',
  },
  uba: {
    title: 'Ingest - External Api - Umweltbundesamt (UBA) Air Data',
    store: 'ingestExternalApiUbaStore',
    list: 'ingestExternalApiUbaList',
  },
};
const metaProvider = providerMetaMap[provider]!;
const rows = computed(() =>
  ((stores[metaProvider.store]?.[metaProvider.list] ?? []) as ExternalApiRow[]).map((r) => ({
    ...r,
    provider,
  })),
);

interface ExternalApiRow {
  provider: string;
  id: number;
  name: string;
  permission_group: { name: string };
}
const columns: QTableColumn<ExternalApiRow>[] = [
  { name: 'provider', label: 'API Type', align: 'left', field: 'provider' },
  {
    name: 'id',
    required: true,
    label: 'ID',
    align: 'left',
    field: (row) => row.id,
    format: (val) => `${val}`,
    sortable: true,
  },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'center' },
  {
    name: 'permission-group',
    label: 'Permission Group',
    field: (row) => row.permission_group.name,
    sortable: true,
    align: 'center',
  },
];

onMounted(async () => {
  await Promise.all(Object.values(stores).map((store) => store.dispatchGetList()));
});

function goBack() {
  triggerSelectionStore.clear();
  router.back();
}
</script>
