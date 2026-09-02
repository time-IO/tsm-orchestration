<template>
  <div>
    <!-- Icon/Btn: Selecting the Visibility of Columns   -->
    <div class="row justify-end q-mb-sm">
      <q-btn flat icon="view_column" label="Columns" color="blue-grey-6">
        <q-menu>
          <q-list style="min-width: 180px">
            <!--            select all-->
            <q-item dense clickable @click="toggleAll">
              <q-item-section side>
                <q-checkbox
                  :model-value="allVisible"
                  @update:model-value="toggleAll"
                  dense
                  color="blue-grey-6"
                />
              </q-item-section>
              <q-item-section><strong>All</strong></q-item-section>
            </q-item>
            <q-separator />
            <q-item
              v-for="opt in columnOptions"
              :key="opt.value"
              dense
              clickable
              @click="toggleColumn(opt.value)"
            >
              <q-item-section side>
                <q-checkbox
                  :model-value="visibleColumns.includes(opt.value)"
                  @update:model-value="toggleColumn(opt.value)"
                  dense
                  color="blue-grey-6"
                />
              </q-item-section>
              <q-item-section>{{ opt.label }}</q-item-section>
            </q-item>
          </q-list>
        </q-menu>
      </q-btn>
    </div>

    <q-table
      ref="tableRef"
      :rows="rows"
      :columns="default_parser_columns"
      :visible-columns="visibleColumns"
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
            :style="`width: ${colWidths[col.name] ? colWidths[col.name] + 'px' : 'auto'}; position: relative; user-select: none;`"
          >
            {{ col.label }}
            <span class="col-resize-handle" @mousedown="startResize($event, col.name)" />
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
            :class="['action', 'created_by'].includes(col.name) ? 'text-center' : 'text-left'"
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
                <q-tooltip>Edit</q-tooltip>
              </q-btn>
              <q-btn
                :to="`${generateParserPath(props.row)}/copy`"
                flat
                outline
                color="black"
                icon="content_copy"
              >
                <q-tooltip>Copy parser</q-tooltip>
              </q-btn>

              <!--            <q-btn-->
              <!--              flat-->
              <!--              outline-->
              <!--              color="negative"-->
              <!--              icon="delete"-->
              <!--              @click="setIdToDeleteAndopenDeleteDialog(props.row.id)"-->
              <!--            >-->
              <!--              <q-tooltip>Delete</q-tooltip>-->
              <!--            </q-btn>-->
            </template>

            <template v-else-if="col.name === 'created_by'">
              <q-icon flat class="text-grey-8" name="las la-user-edit" size="sm">
                <q-tooltip>
                  {{ col.value ?? 'N/A' }}
                </q-tooltip>
              </q-icon>
            </template>

            <template v-else>
              <span
                v-if="col.value !== null && col.value !== undefined && col.value !== ''"
                :style="`display: inline-flex; align-items: center; max-width: ${colWidths[col.name] ? colWidths[col.name] + 'px' : 'auto'}`"
              >
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
                  {{ col.value }}
                  <q-tooltip>{{ col.value }}</q-tooltip>
                </span>
                <q-btn
                  v-if="col.name === 'uuid'"
                  flat
                  round
                  icon="content_copy"
                  size="xs"
                  text-color="grey"
                  @click="copyClipboard(props.row.uuid)"
                >
                  <q-tooltip>Copy UUID</q-tooltip>
                </q-btn>
              </span>
              <span v-else class="text-grey-6"> N/A </span>
            </template>
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
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
import { copyToClipboard, useQuasar } from 'quasar';

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

// const setIdToDeleteAndopenDeleteDialog = (id: number | null) => {
//   idToDelete.value = id;
//   deleteDialog.value = true;
// };

const emitDelete = () => {
  emit('delete', idToDelete.value);
  closeDeleteDialog();
};

const closeDeleteDialog = () => {
  idToDelete.value = null;
  deleteDialog.value = false;
};

const $q = useQuasar();
const copyClipboard = (text: string | null) => {
  if (!text) {
    return;
  }
  copyToClipboard(text)
    .then(() => {
      $q.notify({
        message: 'Copied to clipboard',
        color: 'positive',
        icon: 'check',
      });
    })
    .catch(() => {
      $q.notify({
        message: 'Failed to copy',
        color: 'negative',
        icon: 'error',
      });
    });
};

const windowWidth = ref(window.innerWidth);

window.addEventListener('resize', () => {
  windowWidth.value = window.innerWidth;
});

const colMinWidths: Record<string, number> = {
  id: 40,
  permission_group: 40,
  name: 40,
  uuid: 80,
  ingest_type: 80,
  created_at: 90,
  created_by: 60,
  action: 120,
};

const defaultColWidths: Record<string, number> = {
  id: 60,
  permission_group: windowWidth.value < 1200 ? 80 : 150,
  name: windowWidth.value < 1200 ? 80 : 120,
  uuid: windowWidth.value < 1200 ? 80 : 120,
  ingest_type: 120,
  created_at: 110,
  created_by: 80,
  action: 140,
};

// loading the 'Usersettings'
const savedColWidths = sessionStorage.getItem('parser-col-widths');
// handover the setting
const colWidths = ref<Record<string, number>>(
  savedColWidths
    ? Object.fromEntries(
        Object.entries(JSON.parse(savedColWidths)).map(([key, value]) => [key, Number(value)]),
      )
    : defaultColWidths,
);

// functions for setting a new col-widths
let resizingCol: string | null = null;
let startX = 0;
let startWidth = 0;

function startResize(e: MouseEvent, colName: string) {
  resizingCol = colName;
  startX = e.clientX;

  const th = (e.target as HTMLElement).closest('th');
  startWidth = th ? th.offsetWidth : (colWidths.value[colName] ?? 100);

  document.addEventListener('mousemove', onResize);
  document.addEventListener('mouseup', stopResize);
}

function onResize(e: MouseEvent) {
  if (!resizingCol) return;
  const diff = e.clientX - startX;
  const min = colMinWidths[resizingCol] ?? 50;
  const newWidth = Math.max(min, startWidth + diff);
  colWidths.value[resizingCol] = newWidth;
}

function stopResize() {
  resizingCol = null;
  document.removeEventListener('mousemove', onResize);
  document.removeEventListener('mouseup', stopResize);
  sessionStorage.setItem('parser-col-widths', JSON.stringify(colWidths.value));
}

// to select the visibility of the columns
// except actions
const columnOptions = computed(() =>
  default_parser_columns
    .filter((c) => c.name !== 'action')
    .map((c) => ({ label: c.label, value: c.name })),
);

const savedColumns = sessionStorage.getItem('parser-visible-columns');

const visibleColumns = ref<string[]>(
  savedColumns ? JSON.parse(savedColumns) : default_parser_columns.map((c) => c.name),
);

function toggleColumn(colName: string) {
  if (visibleColumns.value.includes(colName)) {
    visibleColumns.value = visibleColumns.value.filter((c) => c !== colName);
  } else {
    visibleColumns.value = [...visibleColumns.value, colName];
  }
  sessionStorage.setItem('parser-visible-columns', JSON.stringify(visibleColumns.value));
}

const allVisible = computed(() =>
  columnOptions.value.every((opt) => visibleColumns.value.includes(opt.value)),
);

function toggleAll() {
  if (allVisible.value) {
    visibleColumns.value = ['action'];
  } else {
    visibleColumns.value = default_parser_columns.map((c) => c.name);
  }
  sessionStorage.setItem('parser-visible-columns', JSON.stringify(visibleColumns.value));
}
</script>

<style>
thead th {
  min-width: 0 !important;
}
</style>
<style scoped>
.row-highlight {
  background-color: rgba(255, 0, 0, 0.1);
}
.col-resize-handle {
  position: absolute;
  right: 0;
  top: 15%;
  bottom: 15%;
  width: 8px;
  cursor: col-resize;
  background: transparent;
  border-right: 2px solid rgba(0, 0, 0, 0.15);
  transition: border-color 0.15s;
}

.col-resize-handle:hover,
.col-resize-handle:active {
  border-right: 2px solid rgba(0, 0, 0, 0.5);
}
</style>
