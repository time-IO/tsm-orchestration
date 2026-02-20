<template>
  <div class="text-h5 q-mt-lg">{{ title }}</div>
  <q-table :rows="rows" :columns="columns" row-key="name" flat bordered>
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
</template>

<script setup lang="ts">
import type { QTableColumn } from 'quasar';

defineProps({
  title: {
    type: String,
    required: true,
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
</script>

<style scoped></style>
