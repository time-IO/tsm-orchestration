<template>
  <q-page class="q-pa-lg">
    <h5>Overview of Data Ingest</h5>
    <div class="row q-mb-lg">
      <q-space />
      <q-btn color="green" :label="t('newIngest')" to="/ingest/new" />
    </div>

    <div class="text-h5 q-mt-lg">Ingest - External Api - Neutron Monitor</div>
    <q-table
      :rows="ingestExternalApiNeutronMonitorStore.ingestExternalApiNeutronMonitorList"
      :columns="columns"
      row-key="name"
      flat
      bordered
    >
      <template v-slot:body-cell-action="props">
        <q-td :props="props">
          <div>
            <q-btn
              :to="`ingest/external-api-nm/${props.row.id}`"
              flat
              outline
              color="primary"
              icon="visibility"
            >
              <q-tooltip>View details</q-tooltip>
            </q-btn>
            <q-btn
              :to="`ingest/external-api-nm/${props.row.id}/edit`"
              flat
              outline
              color="secondary"
              icon="edit"
            >
              <q-tooltip>Edit thing</q-tooltip>
            </q-btn>
          </div>
        </q-td>
      </template>
    </q-table>

    <div class="text-h5">Ingest - External Api - Umweltbundesamt (UBA) Air Data</div>
    <q-table
      :rows="ingestExternalApiUbaStore.ingestExternalApiUbaList"
      :columns="columns"
      row-key="name"
      flat
      bordered
    >
      <template v-slot:body-cell-action="props">
        <q-td :props="props">
          <div>
            <q-btn
              :to="`ingest/external-api-uba/${props.row.id}`"
              flat
              outline
              color="primary"
              icon="visibility"
            >
              <q-tooltip>View details</q-tooltip>
            </q-btn>
            <q-btn
              :to="`ingest/external-api-uba/${props.row.id}/edit`"
              flat
              outline
              color="secondary"
              icon="edit"
            >
              <q-tooltip>Edit thing</q-tooltip>
            </q-btn>
          </div>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useIngestExternalApiUbaStore } from 'stores/ingestExternalApiUbaStore';
import { onMounted } from 'vue';
import type { QTableColumn } from 'quasar';
import { useIngestExternalApiNeutronMonitorStore } from 'stores/ingestExternalApiNeutronMonitorStore';
const { t } = useI18n();

const ingestExternalApiUbaStore = useIngestExternalApiUbaStore();
const ingestExternalApiNeutronMonitorStore = useIngestExternalApiNeutronMonitorStore();

onMounted(async () => {
  await ingestExternalApiUbaStore.dispatchGetList();
  await ingestExternalApiNeutronMonitorStore.dispatchGetList();
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
