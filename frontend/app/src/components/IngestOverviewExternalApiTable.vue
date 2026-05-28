<template>
  <q-table
    ref="tableRef"
    :rows="rows"
    :columns="props.columns"
    :loading="loading"
    row-key="id"
    flat
    bordered
    v-model:pagination="pagination"
    @request="onRequest"
    v-bind="$attrs"
  >

    <template v-slot:header="props">
      <q-tr :props="props">
        <q-th
          v-for="col in props.cols"
          :key="col.name"
          :props="props"
          :class="col.name === 'action' ? 'text-center' : 'text-left'"
        >
          {{ col.label }}
        </q-th>
      </q-tr>
    </template>

    <template v-slot:loading>
      <q-inner-loading showing color="primary" />
    </template>

    <template v-slot:body="props">
      <q-tr :props="props">
        <q-td v-for="col in props.cols" :key="col.name" :props="props">
          <span v-if="col.value !== null && col.value !== undefined && col.value !== ''">
            {{ col.value }}
          </span>
          <span v-else class="text-grey-6">N/A</span>
        </q-td>
      </q-tr>
    </template>

  </q-table>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import type { QTableRequestProp, QTableRequestPropPagination } from 'src/services/types';
import { default_ingest_external_api_columns } from 'src/utils/pagination_utils';
import type { QTableColumn } from 'quasar';

const props = defineProps({
  rows: {
    type: Array,
    required: true,
  },
  loading: {
    type: Boolean,
    required: true,
  },
  columns: {
    type: Array as () => QTableColumn[],
    default: () => default_ingest_external_api_columns,
  }

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
