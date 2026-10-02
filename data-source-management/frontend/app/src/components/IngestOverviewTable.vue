<template>
  <overview-table-base
    v-model:pagination="pagination"
    :rows="rows"
    :loading="loading"
    :columns="default_ingest_columns"
    storage-key="ingest"
    :cell-tooltip="cellTooltip"
    @on-request="emit('onRequest', $event)"
  >
    <template #action="{ row }">
      <q-btn :to="generateIngestPath(row)" flat outline color="primary" icon="visibility">
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
    </template>
  </overview-table-base>
</template>

<script setup lang="ts">
import type { QTableColumn } from 'quasar';
import type { QTableRequestPropPagination } from '@/services/types';
import {
  default_ingest_columns,
  generateIngestPath,
  formatExternalApiType,
} from '@/utils/pagination_utils';
import OverviewTableBase from '@/components/OverviewTableBase.vue';

defineProps<{ rows: unknown[]; loading: boolean }>();
const pagination = defineModel<QTableRequestPropPagination>('pagination');
const emit = defineEmits(['onRequest']);

function cellTooltip(col: QTableColumn, value: unknown, row: Record<string, unknown>) {
  if (col.name === 'ingest_type' && row.external_api_type) {
    return `${String(value)} – ${formatExternalApiType(row.external_api_type as string)}`;
  }
  return String(value);
}

function visualizationUrl(uuid: string | null) {
  if (!uuid) return '';
  return `${window.location.origin}/visualization/d/${encodeURIComponent(uuid)}?orgId=1`;
}
</script>
