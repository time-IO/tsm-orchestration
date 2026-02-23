<template>
  <q-page class="q-pa-lg">
    <h5>Overview of Data Ingest</h5>
    <div class="row q-mb-lg">
      <q-space />
      <q-btn color="green" :label="t('newIngest')" to="/ingest/new" />
    </div>

    <ingest-overview-table
      title="Ingest - Mqtt"
      ingest-path="ingest/sftp"
      :columns="columns"
      :rows="ingestSftpStore.ingestSftpList"
    />

    <ingest-overview-table
      title="Ingest - Mqtt"
      ingest-path="ingest/mqtt"
      :columns="columns"
      :rows="ingestMqttStore.ingestMqttList"
    />
    <ingest-overview-table
      title="Ingest - External Api - Bosch IoT"
      ingest-path="ingest/external-api-bosch"
      :columns="columns"
      :rows="ingestExternalApiBoschStore.ingestExternalApiBoschList"
    />

    <ingest-overview-table
      title="Ingest - External Api - Deutscher Wetterdienst"
      ingest-path="ingest/external-api-dwd"
      :columns="columns"
      :rows="ingestExternalApiDwdStore.ingestExternalApiDwdList"
    />

    <ingest-overview-table
      title="Ingest - External Api - Neutron Monitor"
      ingest-path="ingest/external-api-nm"
      :columns="columns"
      :rows="ingestExternalApiNeutronMonitorStore.ingestExternalApiNeutronMonitorList"
    />

    <ingest-overview-table
      title="Ingest - External Api - The Things network"
      ingest-path="ingest/external-api-ttn"
      :columns="columns"
      :rows="ingestExternalApiTheThingsNetworkStore.ingestExternalApiTheThingsNetworkList"
    />

    <ingest-overview-table
      title="Ingest - External Api - TSystems"
      ingest-path="ingest/external-api-tsystems"
      :columns="columns"
      :rows="ingestExternalApiTSystemsStore.ingestExternalApiTSystemsList"
    />

    <ingest-overview-table
      title="Ingest - External Api - Umweltbundesamt (UBA) Air Data"
      ingest-path="ingest/external-api-uba"
      :columns="columns"
      :rows="ingestExternalApiUbaStore.ingestExternalApiUbaList"
    />
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { onMounted } from 'vue';
import type { QTableColumn } from 'quasar';
import IngestOverviewTable from 'components/IngestOverviewTable.vue';
import { useIngestExternalApiUbaStore } from 'stores/ingestExternalApiUbaStore';
import { useIngestExternalApiNeutronMonitorStore } from 'stores/ingestExternalApiNeutronMonitorStore';
import { useIngestExternalApiDwdStore } from 'stores/ingestExternalApiDwdStore';
import { useIngestExternalApiBoschStore } from 'stores/ingestExternalApiBoschStore';
import { useIngestExternalApiTheThingsNetworkStore } from 'stores/ingestExternalApiTheThingsNetworkStore';
import { useIngestExternalApiTSystemsStore } from 'stores/ingestExternalApiTSystemsStore';
import { useIngestMqttStore } from 'stores/ingestMqttStore';
import { useIngestSftpStore } from 'stores/ingestSftpStore';
const { t } = useI18n();

const ingestExternalApiUbaStore = useIngestExternalApiUbaStore();
const ingestExternalApiNeutronMonitorStore = useIngestExternalApiNeutronMonitorStore();
const ingestExternalApiDwdStore = useIngestExternalApiDwdStore();
const ingestExternalApiBoschStore = useIngestExternalApiBoschStore();
const ingestExternalApiTheThingsNetworkStore = useIngestExternalApiTheThingsNetworkStore();
const ingestExternalApiTSystemsStore = useIngestExternalApiTSystemsStore();
const ingestMqttStore = useIngestMqttStore();
const ingestSftpStore = useIngestSftpStore();

onMounted(async () => {
  await ingestExternalApiUbaStore.dispatchGetList();
  await ingestExternalApiNeutronMonitorStore.dispatchGetList();
  await ingestExternalApiDwdStore.dispatchGetList();
  await ingestExternalApiBoschStore.dispatchGetList();
  await ingestExternalApiTheThingsNetworkStore.dispatchGetList();
  await ingestExternalApiTSystemsStore.dispatchGetList();
  await ingestMqttStore.dispatchGetList();
  await ingestSftpStore.dispatchGetList();
});

const columns: QTableColumn[] = [
  {
    name: 'id',
    required: true,
    label: 'ID',
    align: 'left',
    field: (row) => row.id,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    name: 'permission-group',
    label: 'Permission Group',
    field: (row) => row.permission_group.name,
    sortable: true,
    align: 'center',
  },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'center' },
  { name: 'action', label: 'Actions', align: 'center', field: () => '' },
];
</script>

<style scoped></style>
