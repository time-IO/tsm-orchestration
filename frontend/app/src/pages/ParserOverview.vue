<template>
  <q-page class="q-pa-lg">
    <h5>Overview of Parsers</h5>
    <div class="row q-mb-lg">
      <q-space />
      <q-btn color="green" label="Add Parser" to="/parser/new" />
    </div>
    <div class="text-h5 q-mt-lg q-mb-sm">Parser - CSV</div>

    <overview-filter
      class="q-mt-md q-mb-md"
      v-model:name="store.filters.name"
      v-model:permission_group_id="store.filters.permission_group_id"
      v-model:date_from="store.filters.date_from"
      v-model:date_to="store.filters.date_to"
      @apply-filters="store.applyFilters"
    />

    <q-table
      ref="tableRef"
      :rows="store.rows"
      :columns="default_ingest_columns"
      row-key="name"
      v-model:pagination="pagination"
      @request="onRequest"
    >
      <template v-slot:body="props">
        <q-tr :props="props" :class="{ 'row-highlight': props.row.id === idToDelete }">
          <q-td v-for="col in props.cols" :key="col.name" :props="props">
            <template v-if="col.name === 'action'">
              <q-btn
                :to="`parser/csv/${props.row.id}`"
                flat
                outline
                color="primary"
                icon="visibility"
              >
                <q-tooltip>View details</q-tooltip>
              </q-btn>
              <q-btn
                :to="`parser/csv/${props.row.id}/edit`"
                flat
                outline
                color="secondary"
                icon="edit"
              >
                <q-tooltip>Edit parser</q-tooltip>
              </q-btn>
              <q-btn
                :to="`parser/csv/${props.row.id}/copy`"
                flat
                outline
                color="black"
                icon="content_copy"
              >
                <q-tooltip>Edit parser</q-tooltip>
              </q-btn>
              <q-btn
                flat
                outline
                color="negative"
                icon="delete"
                @click="setIdToDeleteAndopenDeleteDialog(props.row.id)"
              >
                <q-tooltip>Delete parser</q-tooltip>
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
          <q-btn color="negative" flat label="Delete" @click="deleteItem" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useCsvParserStore } from 'stores/parserCsvStore';
import { default_ingest_columns } from 'src/utils/pagination_utils';
import type { QTableRequestProp } from 'src/services/types';
import OverviewFilter from 'components/OverviewFilter.vue';
import { useQuasar } from 'quasar';

const $q = useQuasar();

const store = useCsvParserStore();

const deleteDialog = ref(false);
const idToDelete = ref<number | null>(null);

const pagination = computed({
  get: () => store.pagination,
  set: (val) => store.setPagination(val),
});

const tableRef = ref();

onMounted(() => {
  // get initial data from server (1st page)
  tableRef.value.requestServerInteraction();
});

async function onRequest(requestProp: QTableRequestProp) {
  await store.onRequest(requestProp);
}

const setIdToDeleteAndopenDeleteDialog = (id: number | null) => {
  idToDelete.value = id;
  deleteDialog.value = true;
};

const closeDeleteDialog = () => {
  idToDelete.value = null;
  deleteDialog.value = false;
};

const deleteItem = async () => {
  if (!idToDelete.value) {
    return;
  }

  try {
    await store.dispatchDelete(idToDelete.value);
    $q.notify({
      position: 'top',
      type: 'positive',
      message: 'Item deleted successfully',
    });
    await store.dispatchGetList()
  } catch (error) {
    // @ts-expect-error to avoid complicated checks just for type safety, we ignore
    let errorCaption = error?.response?.data?.detail || '';

    // if it is a validation error, then error.response.data.detail is an array of objects [{type:string, loc: string[], msg: string, input: any, probably an object}]
    if (typeof errorCaption === 'object') {
      errorCaption = errorCaption[0].msg;
    }
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to delete item',
      caption: errorCaption,
    });
  } finally {
    deleteDialog.value = false;
  }
};
</script>

<style scoped>
.row-highlight {
  background-color: rgba(255, 0, 0, 0.1);
}
</style>
