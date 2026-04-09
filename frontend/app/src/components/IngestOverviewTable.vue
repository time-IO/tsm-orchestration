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
      row-key="id"
      flat
      bordered
      v-model:pagination="pagination"
      @request="onRequest"
      v-bind="$attrs"
    >
      <template v-slot:body="props">
        <q-tr :props="props" :class="{ 'row-highlight': props.row.id === idToDelete }">
          <q-td v-for="col in props.cols" :key="col.name" :props="props">
            <template v-if="col.name === 'action'">
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
              <q-btn
                :to="`${ingestPath}/${props.row.id}/copy`"
                flat
                outline
                color="black"
                icon="content_copy"
              >
                <q-tooltip>Copy Ingest</q-tooltip>
              </q-btn>
              <q-btn
                flat
                outline
                color="negative"
                icon="delete"
                @click="setIdToDeleteAndopenDeleteDialog(props.row.id)"
              >
                <q-tooltip>Delete Ingest</q-tooltip>
              </q-btn>
            </template>
            <template v-else>
              {{ col.value }}
            </template>
          </q-td>
        </q-tr>
      </template>
    </q-table>
    <q-dialog v-model="deleteDialog" persistent>
      <q-card>
        <q-card-section>
          <h6 class="q-mt-none">Confirm Delete</h6>
        </q-card-section>

        <q-card-section> Are you sure you want to delete this item? </q-card-section>

        <q-card-actions align="right">
          <q-btn color="primary" flat label="Cancel" @click="closeDeleteDialog" />
          <q-space />
          <q-btn color="negative" flat label="Delete" @click="emitDelete" />
        </q-card-actions>
      </q-card>
    </q-dialog>
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

const emit = defineEmits(['onRequest', 'delete']);
const tableRef = ref();

const deleteDialog = ref(false);
const idToDelete = ref<number | null>(null);

onMounted(() => {
  // get initial data from server (1st page)
  tableRef.value.requestServerInteraction();
});

function onRequest(props: QTableRequestProp) {
  emit('onRequest', props);
}

const setIdToDeleteAndopenDeleteDialog = (id: number | null) => {
  idToDelete.value = id;
  deleteDialog.value = true;
};

const emitDelete = () => {
  emit('delete', idToDelete.value);
  closeDeleteDialog()
};

const closeDeleteDialog = () => {
  idToDelete.value = null;
  deleteDialog.value = false;
};
</script>

<style scoped>
.row-highlight {
  background-color: rgba(255, 0, 0, 0.1);
}
</style>
