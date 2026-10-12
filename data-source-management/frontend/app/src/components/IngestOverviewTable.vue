<template>
  <overview-table
    :rows="rows"
    :loading="loading"
    :columns="default_ingest_columns"
    storage-key="ingest"
    :col-min-widths="colMinWidths"
    :default-col-widths="defaultColWidths"
    v-model:pagination="pagination"
    @request="onRequest"
    @delete="onDelete"
    :table-style="'table-layout: fixed; width: 100%'"
  >
    <template #actions="{ row }">
      <q-btn :to="`${generateIngestPath(row)}`" flat outline color="primary" icon="visibility">
        <q-tooltip>View details</q-tooltip>
      </q-btn>
      <q-btn :to="`${generateIngestPath(row)}/edit`" flat outline color="secondary" icon="edit">
        <q-tooltip>Edit</q-tooltip>
      </q-btn>
      <q-btn :to="`${generateIngestPath(row)}/copy`" flat outline color="black" icon="content_copy">
        <q-tooltip>Copy Ingest</q-tooltip>
      </q-btn>

      <q-btn
        :href="visualizationUrl(row.uuid)"
        flat
        outline
        icon="img:icons/grafana_icon.png"
        target="_blank"
      >
        <q-tooltip>Visualization Link</q-tooltip>
      </q-btn>

      <!--            <q-btn-->
      <!--              flat-->
      <!--              outline-->
      <!--              color="negative"-->
      <!--              icon="delete"-->
      <!--              @click="openDeleteDialog(row.id)"-->
      <!--            >-->
      <!--              <q-tooltip>Delete</q-tooltip>-->
      <!--            </q-btn>-->
    </template>

    <template #value-tooltip="{ col, row }">
      {{
        col.name === 'ingest_type' && row.external_api_type
          ? col.value + ' – ' + formatExternalApiType(row.external_api_type)
          : col.value
      }}
    </template>
  </overview-table>
</template>

<script setup lang="ts">
import type { QTableRequestProp, QTableRequestPropPagination } from '@/services/types';
import {
  default_ingest_columns,
  generateIngestPath,
  formatExternalApiType,
} from '@/utils/pagination_utils';
import OverviewTable from '@/components/common/OverviewTable.vue';

defineProps({
  rows: {
    type: Array,
    required: true,
  },
  loading: {
    type: Boolean,
    required: true,
  },
});

const pagination = defineModel<QTableRequestPropPagination>('pagination');

const emit = defineEmits(['onRequest', 'delete']);

function onRequest(props: QTableRequestProp) {
  emit('onRequest', props);
}

const onDelete = (id: number | null, closeDialog: () => void) => {
  emit('delete', id);
  closeDialog();
};

const isSmallWindow = window.innerWidth < 1200;

const colMinWidths: Record<string, number> = {
  id: 40,
  permission_group: 40,
  name: 40,
  uuid: 80,
  ingest_type: 80,
  created_at: 90,
  created_by: 60,
  action: 120,
};

const defaultColWidths: Record<string, number> = {
  id: 60,
  permission_group: isSmallWindow ? 80 : 150,
  name: isSmallWindow ? 80 : 120,
  uuid: isSmallWindow ? 80 : 120,
  ingest_type: 120,
  created_at: 110,
  created_by: 80,
  action: 140,
};

function visualizationUrl(uuid: string | null) {
  if (!uuid) return '';
  return `${window.location.origin}/visualization/d/${encodeURIComponent(uuid)}?orgId=1`;
}
</script>
