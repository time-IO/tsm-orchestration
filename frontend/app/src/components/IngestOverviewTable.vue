<template>
  <div class="q-mb-xl">
    <div class="row items-center q-mb-xs">
      <div class="text-h5" v-if="title">{{ title }}</div>
      <q-space />
      <slot name="actions" />
    </div>
    <q-table
      ref="tableRef"
      :rows="rows"
      :columns="columns"
      row-key="name"
      flat
      bordered
      v-model:pagination="pagination"
      @request="onRequest"
      v-bind="$attrs"
    >
      <template v-slot:body-cell-action="props">
        <q-td :props="props">
          <div>
            <q-btn
              :to="`${ingestPath}/${props.row.id}`"
              flat
              outline
              color="primary"
              icon="visibility"
            >
              <q-tooltip>View details</q-tooltip>
            </q-btn>
            <q-btn
              :to="`${ingestPath}/${props.row.id}/edit`"
              flat
              outline
              color="secondary"
              icon="edit"
            >
              <q-tooltip>Edit Ingest</q-tooltip>
            </q-btn>
          </div>
        </q-td>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import type { QTableColumn } from 'quasar';
import type { QTableRequestProp, QTableRequestPropPagination } from 'src/services/types';

defineProps({
  title: {
    type: String,
    required: false,
  },
  rows: {
    type: Array,
    required: true,
  },
  columns: {
    type: Array<QTableColumn>,
    required: true,
  },
  ingestPath: {
    type: String,
    required: true,
  },
});

const pagination = defineModel<QTableRequestPropPagination>('pagination');

const emit = defineEmits(['onRequest']);
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
