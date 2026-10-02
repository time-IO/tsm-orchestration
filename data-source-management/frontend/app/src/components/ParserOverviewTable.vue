<template>
  <overview-table-base
    v-model:pagination="pagination"
    :rows="rows"
    :loading="loading"
    :columns="default_parser_columns"
    storage-key="parser"
    @on-request="emit('onRequest', $event)"
  >
    <template #action="{ row }">
      <q-btn :to="generateParserPath(row)" flat outline color="primary" icon="visibility">
        <q-tooltip>View details</q-tooltip>
      </q-btn>
      <q-btn :to="`${generateParserPath(row)}/edit`" flat outline color="secondary" icon="edit">
        <q-tooltip>Edit</q-tooltip>
      </q-btn>
      <q-btn :to="`${generateParserPath(row)}/copy`" flat outline color="black" icon="content_copy">
        <q-tooltip>Copy parser</q-tooltip>
      </q-btn>
    </template>
  </overview-table-base>
</template>

<script setup lang="ts">
import type { QTableRequestPropPagination } from '@/services/types';
import { default_parser_columns, generateParserPath } from '@/utils/pagination_utils';
import OverviewTableBase from '@/components/OverviewTableBase.vue';

defineProps<{ rows: unknown[]; loading: boolean }>();
const pagination = defineModel<QTableRequestPropPagination>('pagination');
const emit = defineEmits(['onRequest']);
</script>
