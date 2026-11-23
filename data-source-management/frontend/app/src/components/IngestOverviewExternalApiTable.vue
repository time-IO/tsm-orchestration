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

const columnWidths: ColumnWidths = {
  id: { min: 5, default: 7 },
  permission_group: { min: 5, default: 17 },
  name: { min: 5, default: 14 },
  api_type: { min: 9, default: 19 },
  created_at: { min: 10, default: 13 },
  uuid: { min: 9, default: 14 },
};
</script>
