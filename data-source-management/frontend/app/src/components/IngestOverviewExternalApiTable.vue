<template>
  <overview-table-base
    v-model:pagination="pagination"
    :rows="rows"
    :loading="loading"
    :columns="columns"
    storage-key="ingestExtApi"
    @on-request="emit('onRequest', $event)"
  />
</template>

<script setup lang="ts">
import type { QTableColumn } from 'quasar';
import type { QTableRequestPropPagination } from '@/services/types';
import { default_ingest_external_api_columns } from '@/utils/pagination_utils';
import OverviewTableBase from "@/components/OverviewTableBase.vue";

withDefaults(
  defineProps<{ rows: unknown[]; loading: boolean; columns?: QTableColumn[] }>(),
  { columns: () => default_ingest_external_api_columns },
);
const pagination = defineModel<QTableRequestPropPagination>('pagination');
const emit = defineEmits(['onRequest']);
</script>
