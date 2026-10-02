<template>
  <div>
    <div class="row justify-end q-mb-sm">
      <q-btn flat icon="view_column" label="Columns" color="blue-grey-6">
        <q-menu>
          <q-list style="min-width: 180px">
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
      :columns="columns"
      :visible-columns="visibleColumns"
      :loading="loading"
      row-key="id"
      flat
      bordered
      v-model:pagination="pagination"
      @request="onRequest"
      :selection="selectable ? 'multiple' : 'none'"
      v-model:selected="selected"
      :class="{ 'overview-table--selectable': selectable }"
      v-bind="$attrs"
    >
      <template v-slot:header="props">
        <q-tr :props="props">
          <!-- Selection / Checkbox Header -->
          <q-th v-if="selectable" auto-width>
            <q-checkbox v-model="props.selected" :indeterminate="props.selected === null" />
          </q-th>

          <q-th
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
            :data-col="col.name"
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
          <q-td v-if="selectable" auto-width>
            <q-checkbox v-model="props.selected" />
          </q-td>
          <q-td
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
            :class="['action', 'created_by'].includes(col.name) ? 'text-center' : 'text-left'"
          >
            <template v-if="col.name === 'action'">
              <slot name="actions" :row="props.row" :open-delete-dialog="openDeleteDialog" />
            </template>

            <template v-else-if="col.name === 'created_by'">
              <q-icon flat class="text-grey-8" name="las la-user-edit" size="sm">
                <q-tooltip>{{ col.value ?? 'N/A' }}</q-tooltip>
              </q-icon>
            </template>

            <template v-else>
              <div
                v-if="col.value !== null && col.value !== undefined && col.value !== ''"
                :style="colWidths[col.name] ? 'width: 0; min-width: 100%' : ''"
              >
                <span style="display: inline-flex; align-items: center; max-width: 100%">
                  <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
                    {{ col.value }}
                    <q-tooltip>
                      <slot name="value-tooltip" :col="col" :row="props.row">{{ col.value }}</slot>
                    </q-tooltip>
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
              </div>
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

<script setup lang="ts" generic="Row">
import { computed, onMounted, ref } from 'vue';
import type { QTableColumn } from 'quasar';
import { copyToClipboard, useQuasar } from 'quasar';
import type { QTableRequestProp, QTableRequestPropPagination } from '@/services/types';

const props = withDefaults(
  defineProps<{
    rows: Row[];
    loading: boolean;
    columns: QTableColumn[];
    // prefix of the sessionStorage keys for column widths and visibility
    storageKey: string;
    colMinWidths: Record<string, number>;
    defaultColWidths: Record<string, number>;
    selectable?: boolean;
  }>(),
  { selectable: false },
);

const pagination = defineModel<QTableRequestPropPagination | undefined>('pagination');
const selected = defineModel<Row[] | undefined>('selected');

const emit = defineEmits<{
  request: [props: QTableRequestProp];
  // `closeDialog` lets the parent decide when the confirm dialog is closed
  delete: [id: number | null, closeDialog: () => void];
}>();
const tableRef = ref();

const deleteDialog = ref(false);
const idToDelete = ref<number | null>(null);

onMounted(() => {
  // get initial data from server (1st page)
  tableRef.value.requestServerInteraction();
});

function onRequest(props: QTableRequestProp) {
  emit('request', props);
}

const openDeleteDialog = (id: number | null) => {
  idToDelete.value = id;
  deleteDialog.value = true;
};

const emitDelete = () => {
  emit('delete', idToDelete.value, closeDeleteDialog);
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

const colWidthsStorageKey = `${props.storageKey}-col-widths`;
const visibleColumnsStorageKey = `${props.storageKey}-visible-columns`;

// loading the 'Usersettings'
const savedColWidths = sessionStorage.getItem(colWidthsStorageKey);
// handover the setting
const colWidths = ref<Record<string, number>>(
  savedColWidths
    ? Object.fromEntries(
        Object.entries(JSON.parse(savedColWidths)).map(([key, value]) => [key, Number(value)]),
      )
    : { ...props.defaultColWidths },
);

const minWidthOf = (colName: string) => props.colMinWidths[colName] ?? 50;

// functions for setting a new col-widths per mousemove
let resizingCol: string | null = null;
let startX = 0;
let startWidths: Record<string, number> = {};
let otherCols: string[] = [];

function startResize(e: MouseEvent, colName: string) {
  resizingCol = colName;
  startX = e.clientX;

  const headerRow = (e.target as HTMLElement).closest('tr');
  const ths = headerRow ? Array.from(headerRow.querySelectorAll<HTMLElement>('th[data-col]')) : [];
  ths.forEach((th) => {
    colWidths.value[th.dataset.col!] = th.getBoundingClientRect().width;
  });
  startWidths = { ...colWidths.value };
  otherCols = ths.map((th) => th.dataset.col!).filter((c) => c !== colName);

  document.addEventListener('mousemove', onResize);
  document.addEventListener('mouseup', stopResize);
}

function onResize(e: MouseEvent) {
  if (!resizingCol) return;
  const diff = e.clientX - startX;
  colWidths.value = { ...startWidths };
  const startWidth = startWidths[resizingCol] ?? 100;
  const newWidth = Math.max(minWidthOf(resizingCol), startWidth + diff);
  colWidths.value[resizingCol] = newWidth;

  const widthDelta = newWidth - startWidth;
  if (widthDelta > 0) {
    reclaimWidth(widthDelta, otherCols);
  } else {
    distributeWidth(Math.abs(widthDelta), otherCols);
  }
}

function stopResize() {
  const preventSortTrigger = (ev: MouseEvent) => {
    ev.stopPropagation();
    document.removeEventListener('click', preventSortTrigger, true);
  };
  document.addEventListener('click', preventSortTrigger, true);
  resizingCol = null;
  document.removeEventListener('mousemove', onResize);
  document.removeEventListener('mouseup', stopResize);
  sessionStorage.setItem(colWidthsStorageKey, JSON.stringify(colWidths.value));
}

// to select the visibility of the columns
// except actions
const columnOptions = computed(() =>
  props.columns.filter((c) => c.name !== 'action').map((c) => ({ label: c.label, value: c.name })),
);

const savedColumns = sessionStorage.getItem(visibleColumnsStorageKey);

const visibleColumns = ref<string[]>(
  savedColumns ? JSON.parse(savedColumns) : props.columns.map((c) => c.name),
);

const sumWidths = (colNames: string[]) =>
  colNames.reduce((sum, c) => sum + (colWidths.value[c] ?? 0), 0);

const withWidth = (colNames: string[]) => colNames.filter((c) => colWidths.value[c] !== undefined);

function distributeWidth(amount: number, receivers: string[]) {
  const targets = withWidth(receivers);
  if (amount <= 0 || targets.length === 0) return;
  const share = amount / targets.length;
  targets.forEach((c) => {
    if (!colWidths.value[c]) {
      return;
    }
    colWidths.value[c] += share;
  });
}

// looping through remaining cols and remaining with to evenly distribute space
function reclaimWidth(amount: number, donors: string[]) {
  let remaining = amount;
  const hasBuffer = (c: string) => colWidths.value[c]! > minWidthOf(c) + 0.5;
  let candidates = withWidth(donors).filter(hasBuffer);
  while (remaining > 0.5 && candidates.length > 0) {
    const share = remaining / candidates.length;
    for (const c of candidates) {
      const take = Math.min(share, colWidths.value[c]! - minWidthOf(c));
      colWidths.value[c] = colWidths.value[c]! - take;
      remaining -= take;
    }
    candidates = candidates.filter(hasBuffer);
  }
}

function setVisibleColumns(newVisibleColumns: string[]) {
  const hidden = visibleColumns.value.filter((c) => !newVisibleColumns.includes(c));
  const shown = newVisibleColumns.filter((c) => !visibleColumns.value.includes(c));
  const remaining = visibleColumns.value.filter((c) => newVisibleColumns.includes(c));

  distributeWidth(sumWidths(hidden), remaining);
  reclaimWidth(sumWidths(shown), remaining);

  visibleColumns.value = newVisibleColumns;
  sessionStorage.setItem(visibleColumnsStorageKey, JSON.stringify(visibleColumns.value));
  sessionStorage.setItem(colWidthsStorageKey, JSON.stringify(colWidths.value));
}

function toggleColumn(colName: string) {
  if (visibleColumns.value.includes(colName)) {
    setVisibleColumns(visibleColumns.value.filter((c) => c !== colName));
  } else {
    setVisibleColumns([...visibleColumns.value, colName]);
  }
}

const allVisible = computed(() =>
  columnOptions.value.every((opt) => visibleColumns.value.includes(opt.value)),
);

function toggleAll() {
  if (allVisible.value) {
    setVisibleColumns(['action']);
  } else {
    setVisibleColumns(props.columns.map((c) => c.name));
  }
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

.overview-table--selectable .q-table th:first-child,
.overview-table--selectable .q-table td:first-child {
  padding-left: 0;
  padding-right: 0;
  text-align: center;
  vertical-align: middle;
}
</style>
