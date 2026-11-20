<template>
  <overview-table
    :rows="rows"
    :loading="loading"
    :columns="default_parser_columns"
    storage-key="parser"
    :column-widths="columnWidths"
    v-model:pagination="pagination"
    @request="onRequest"
    @delete="onDelete"
  >
    <template #actions="{ row }">
      <q-btn :to="`${generateParserPath(row)}`" flat outline color="primary" icon="visibility">
        <q-tooltip>View details</q-tooltip>
      </q-btn>
      <q-btn :to="`${generateParserPath(row)}/edit`" flat outline color="secondary" icon="edit">
        <q-tooltip>Edit</q-tooltip>
      </q-btn>
      <q-btn :to="`${generateParserPath(row)}/copy`" flat outline color="black" icon="content_copy">
        <q-tooltip>Copy parser</q-tooltip>
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
  </overview-table>
</template>

<script setup lang="ts">
import { default_parser_columns, generateParserPath } from '@/utils/pagination_utils';
import type { QTableRequestProp, QTableRequestPropPagination } from '@/services/types';
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

const columnWidths: ColumnWidths = {
  id: { min: 6, max: 6, default: 6 },
  permission_group: { min: 8, default: 17 },
  name: { min: 3, default: 28 },
  parser_type: { min: 5, default: 8 },
  created_at: { min: 6, default: 9 },
  created_by: { min: 5, default: 8 },
  uuid: { min: 3, default: 13 },
  action: { min: 11, max: 11, default: 11 },
};
</script>
