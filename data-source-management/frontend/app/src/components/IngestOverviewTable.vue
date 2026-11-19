<template>
  <overview-table
    :rows="rows"
    :loading="loading"
    :columns="default_ingest_columns"
    storage-key="ingest"
    :column-widths="columnWidths"
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
import type { ColumnWidths } from '@/utils/overview_table_utils';

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

const columnWidths: ColumnWidths = {
  id: { min: 40, default: 60 },
  permission_group: { min: 40, default: isSmallWindow ? 80 : 150 },
  name: { min: 40, default: isSmallWindow ? 80 : 120 },
  uuid: { min: 80, default: isSmallWindow ? 80 : 120 },
  ingest_type: { min: 80, default: 120 },
  created_at: { min: 90, default: 110 },
  created_by: { min: 60, default: 80 },
  action: { min: 120, default: 140 },
};

function visualizationUrl(uuid: string | null) {
  if (!uuid) return '';
  return `${window.location.origin}/visualization/d/${encodeURIComponent(uuid)}?orgId=1`;
}
</script>
