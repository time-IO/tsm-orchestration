<template>
  <q-table
    ref="tableRef"
    :rows="rows"
    :columns="default_ingest_external_api_columns"
    :loading="loading"
    row-key="id"
    flat
    bordered
    v-model:pagination="pagination"
    @request="onRequest"
    v-bind="$attrs"
  >
    <template v-slot:loading>
      <q-inner-loading showing color="primary" />
    </template>
  </q-table>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import type { QTableRequestProp, QTableRequestPropPagination } from 'src/services/types';
import { default_ingest_external_api_columns } from 'src/utils/pagination_utils';

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
const tableRef = ref();

onMounted(() => {
  // get initial data from server (1st page)
  tableRef.value.requestServerInteraction();
});

function onRequest(props: QTableRequestProp) {
  emit('onRequest', props);
}
</script>

<style scoped></style>
