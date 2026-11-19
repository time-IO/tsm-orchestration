<template>
  <overview-table
    :rows="rows"
    :loading="loading"
    :columns="columns"
    storage-key="ingest-external-api"
    :column-widths="columnWidths"
    :rows-per-page-options="rowsPerPageOptions"
    :selectable="selectable"
    v-model:pagination="pagination"
    v-model:selected="selected"
    @request="onRequest"
  />
</template>

<script setup lang="ts">
import type { QTableColumn } from 'quasar';
import OverviewTable from '@/components/common/OverviewTable.vue';
import type { IngestExternalApiRead } from '@/services/ingest_external_api/types';
import type { QTableRequestProp, QTableRequestPropPagination } from '@/services/types';
import type { ColumnWidths } from '@/utils/overview_table_utils';
import { default_ingest_external_api_columns } from '@/utils/pagination_utils';

const {
  rows,
  loading,
  columns = default_ingest_external_api_columns,
  rowsPerPageOptions = [10, 25, 50, 100, 200],
  selectable = false,
} = defineProps<{
  rows: IngestExternalApiRead[];
  loading: boolean;
  columns?: QTableColumn[];
  rowsPerPageOptions?: number[];
  selectable?: boolean;
}>();

const pagination = defineModel<QTableRequestPropPagination>('pagination');
const selected = defineModel<IngestExternalApiRead[]>('selected');

const emit = defineEmits<{
  onRequest: [props: QTableRequestProp];
}>();

function onRequest(props: QTableRequestProp) {
  emit('onRequest', props);
}

const isSmallWindow = window.innerWidth < 1200;

const columnWidths: ColumnWidths = {
  id: { min: 40, default: 60 },
  permission_group: { min: 40, default: isSmallWindow ? 80 : 150 },
  name: { min: 40, default: isSmallWindow ? 80 : 120 },
  api_type: { min: 80, default: 160 },
  created_at: { min: 90, default: 110 },
  uuid: { min: 80, default: isSmallWindow ? 80 : 120 },
  action: { min: 140, max: 140, default: 140 },
};
</script>
