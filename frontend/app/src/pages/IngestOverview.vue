<template>
  <q-page class="q-pa-lg">
    <h5>Overview of Data Ingest</h5>
    <div class="row q-mb-lg">
      <q-space />
      <q-btn color="green" :label="t('newIngest')" to="/ingest/new" />
    </div>

    <ingest-overview-table
      title="Ingest - SFTP"
      ingest-path="ingest/sftp"
      :columns="columns"
      :rows="ingestSftpStore.ingestSftpList"
      @onRequest="loadIngestSftp"
      v-model:pagination="paginationIngestSftp"
    />

    <ingest-overview-table
      title="Ingest - Mqtt"
      ingest-path="ingest/mqtt"
      :columns="columns"
      :rows="ingestMqttStore.ingestMqttList"
      @onRequest="loadIngestMqtt"
      v-model:pagination="paginationIngestMqtt"
    />
    <ingest-overview-table
      title="Ingest - External Api - Bosch IoT"
      ingest-path="ingest/external-api-bosch"
      :columns="columns"
      :rows="ingestExternalApiBoschStore.ingestExternalApiBoschList"
      @onRequest="loadIngestExternalApiBosch"
      v-model:pagination="paginationIngestExternalApiBosch"
    />

    <ingest-overview-table
      title="Ingest - External Api - Deutscher Wetterdienst"
      ingest-path="ingest/external-api-dwd"
      :columns="columns"
      :rows="ingestExternalApiDwdStore.ingestExternalApiDwdList"
      @onRequest="loadIngestExternalApiDwd"
      v-model:pagination="paginationIngestExternalApiDwd"
    />

    <ingest-overview-table
      title="Ingest - External Api - Neutron Monitor"
      ingest-path="ingest/external-api-nm"
      :columns="columns"
      :rows="ingestExternalApiNeutronMonitorStore.ingestExternalApiNeutronMonitorList"
      @onRequest="loadIngestExternalApiNeutronMonitor"
      v-model:pagination="paginationIngestExternalApiNeutronMonitor"
    />

    <ingest-overview-table
      title="Ingest - External Api - The Things network"
      ingest-path="ingest/external-api-ttn"
      :columns="columns"
      :rows="ingestExternalApiTheThingsNetworkStore.ingestExternalApiTheThingsNetworkList"
      @onRequest="loadIngestExternalApiTheThingsNetwork"
      v-model:pagination="paginationIngestExternalApiTheThingsNetwork"
    />

    <ingest-overview-table
      title="Ingest - External Api - TSystems"
      ingest-path="ingest/external-api-tsystems"
      :columns="columns"
      :rows="ingestExternalApiTSystemsStore.ingestExternalApiTSystemsList"
      @onRequest="loadIngestExternalApiTSystems"
      v-model:pagination="paginationIngestExternalApiTSystems"
    />

    <ingest-overview-table
      title="Ingest - External Api - Umweltbundesamt (UBA) Air Data"
      ingest-path="ingest/external-api-uba"
      :columns="columns"
      :rows="ingestExternalApiUbaStore.ingestExternalApiUbaList"
      @onRequest="loadIngestExternalApiUba"
      v-model:pagination="paginationIngestExternalApiUba"
    />

    <ingest-overview-table
      title="Ingest - External SFTP"
      ingest-path="ingest/external-sftp"
      :columns="columns"
      :rows="ingestExternalSftpStore.ingestExternalSftpList"
      @onRequest="loadIngestExternalSftp"
      v-model:pagination="paginationIngestExternalSftp"
    />
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { ref } from 'vue';
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
import { useIngestExternalSftpStore } from 'stores/ingestExternalSftpStore';
import type { QTableRequestProp, QTableRequestPropPagination } from 'src/services/types';
import { defaultPagination, updatePagination } from 'src/utils/pagination_utils';
const { t } = useI18n();

const ingestExternalApiUbaStore = useIngestExternalApiUbaStore();
const ingestExternalApiNeutronMonitorStore = useIngestExternalApiNeutronMonitorStore();
const ingestExternalApiDwdStore = useIngestExternalApiDwdStore();
const ingestExternalApiBoschStore = useIngestExternalApiBoschStore();
const ingestExternalApiTheThingsNetworkStore = useIngestExternalApiTheThingsNetworkStore();
const ingestExternalApiTSystemsStore = useIngestExternalApiTSystemsStore();
const ingestMqttStore = useIngestMqttStore();
const ingestSftpStore = useIngestSftpStore();
const ingestExternalSftpStore = useIngestExternalSftpStore();

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

const paginationIngestSftp = ref<QTableRequestPropPagination>(defaultPagination);

const paginationIngestMqtt = ref<QTableRequestPropPagination>(defaultPagination);

const paginationIngestExternalApiBosch = ref<QTableRequestPropPagination>(defaultPagination);

const paginationIngestExternalApiDwd = ref<QTableRequestPropPagination>(defaultPagination);

const paginationIngestExternalApiNeutronMonitor =
  ref<QTableRequestPropPagination>(defaultPagination);

const paginationIngestExternalApiTheThingsNetwork =
  ref<QTableRequestPropPagination>(defaultPagination);

const paginationIngestExternalApiTSystems = ref<QTableRequestPropPagination>(defaultPagination);

const paginationIngestExternalApiUba = ref<QTableRequestPropPagination>(defaultPagination);

const paginationIngestExternalSftp = ref<QTableRequestPropPagination>(defaultPagination);

async function loadIngestSftp(requestProp: QTableRequestProp) {
  const { page, rowsPerPage } = requestProp.pagination;
  const data = await ingestSftpStore.dispatchGetList(page, rowsPerPage);
  updatePagination(paginationIngestSftp, data);
}
async function loadIngestMqtt(requestProp: QTableRequestProp) {
  const { page, rowsPerPage } = requestProp.pagination;
  const data = await ingestMqttStore.dispatchGetList(page, rowsPerPage);
  updatePagination(paginationIngestMqtt, data);
}
async function loadIngestExternalApiBosch(requestProp: QTableRequestProp) {
  const { page, rowsPerPage } = requestProp.pagination;
  const data = await ingestExternalApiBoschStore.dispatchGetList(page, rowsPerPage);
  updatePagination(paginationIngestExternalApiBosch, data);
}
async function loadIngestExternalApiDwd(requestProp: QTableRequestProp) {
  const { page, rowsPerPage } = requestProp.pagination;
  const data = await ingestExternalApiDwdStore.dispatchGetList(page, rowsPerPage);
  updatePagination(paginationIngestExternalApiDwd, data);
}
async function loadIngestExternalApiNeutronMonitor(requestProp: QTableRequestProp) {
  const { page, rowsPerPage } = requestProp.pagination;
  const data = await ingestExternalApiNeutronMonitorStore.dispatchGetList(page, rowsPerPage);
  updatePagination(paginationIngestExternalApiNeutronMonitor, data);
}
async function loadIngestExternalApiTheThingsNetwork(requestProp: QTableRequestProp) {
  const { page, rowsPerPage } = requestProp.pagination;
  const data = await ingestExternalApiTheThingsNetworkStore.dispatchGetList(page, rowsPerPage);
  updatePagination(paginationIngestExternalApiTheThingsNetwork, data);
}
async function loadIngestExternalApiTSystems(requestProp: QTableRequestProp) {
  const { page, rowsPerPage } = requestProp.pagination;
  const data = await ingestExternalApiTSystemsStore.dispatchGetList(page, rowsPerPage);
  updatePagination(paginationIngestExternalApiTSystems, data);
}
async function loadIngestExternalApiUba(requestProp: QTableRequestProp) {
  const { page, rowsPerPage } = requestProp.pagination;
  const data = await ingestExternalApiUbaStore.dispatchGetList(page, rowsPerPage);
  updatePagination(paginationIngestExternalApiUba, data);
}
async function loadIngestExternalSftp(requestProp: QTableRequestProp) {
  const { page, rowsPerPage } = requestProp.pagination;
  const data = await ingestExternalSftpStore.dispatchGetList(page, rowsPerPage);
  updatePagination(paginationIngestExternalSftp, data);
}
</script>

<style scoped></style>
