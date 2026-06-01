<template>
  <q-table
    ref="tableRef"
    :rows="rows"
    :columns="default_parser_columns"
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
      <q-tr :props="props" :class="{ 'row-highlight': props.row.id === idToDelete }">
        <q-td
          v-for="col in props.cols"
          :key="col.name"
          :props="props"
          :class="col.name === 'action' ? 'text-center' : 'text-left'"
        >
          <template v-if="col.name === 'action'">
            <q-btn
              :to="`${generateParserPath(props.row)}`"
              flat
              outline
              color="primary"
              icon="visibility"
            >
              <q-tooltip>View details</q-tooltip>
            </q-btn>
            <q-btn
              :to="`${generateParserPath(props.row)}/edit`"
              flat
              outline
              color="secondary"
              icon="edit"
            >
              <q-tooltip>Edit parser</q-tooltip>
            </q-btn>
            <q-btn
              :to="`${generateParserPath(props.row)}/copy`"
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
            <span v-if="col.value !== null && col.value !== undefined && col.value !== ''">
              <div
                :style="`overflow: hidden;
              text-overflow: ellipsis;
              hite-space: nowrap;
             max-width: ${getMaxWidth(col.field)}`"
              >
                {{ col.value }}
                <q-tooltip>{{ col.value }}</q-tooltip>
              </div>
            </span>
            <span v-else class="text-grey-6"> N/A </span>
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
</template>

<script setup lang="ts">
import { default_parser_columns, generateParserPath } from 'src/utils/pagination_utils';
import type { QTableRequestProp, QTableRequestPropPagination } from 'src/services/types';
import { computed, onMounted, ref } from 'vue';

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
  closeDeleteDialog();
};

const closeDeleteDialog = () => {
  idToDelete.value = null;
  deleteDialog.value = false;
};

const windowWidth = ref(window.innerWidth);

window.addEventListener('resize', () => {
  windowWidth.value = window.innerWidth;
});

const colMaxWidth: Record<string, { sm: string; lg: string }> = {
  permission_group: { sm: '80px', lg: '150px' },
  name: { sm: '80px', lg: '220px' },
};

const getMaxWidth = computed(() => (colName: string) => {
  const widths = colMaxWidth[colName];
  if (!widths) return 'auto';
  return windowWidth.value < 1200 ? widths.sm : widths.lg;
});
</script>

<style scoped>
.row-highlight {
  background-color: rgba(255, 0, 0, 0.1);
}
</style>
