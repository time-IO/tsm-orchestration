<template>
  <div :class="{ 'column no-wrap overview-table--fill': virtualScroll }">
    <div class="row no-wrap items-center q-mb-sm" style="gap: 8px">
      <slot name="toolbar" />
      <q-space />
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
      :row-key="rowKey"
      flat
      bordered
      :dense="dense"
      :table-style="tableStyle"
      :virtual-scroll="virtualScroll"
      :virtual-scroll-sticky-size-start="dense ? 33 : 48"
      :style="{ '--overview-table-min-width': `${minTableWidth}px` }"
      v-model:pagination="pagination"
      :rows-per-page-options="rowsPerPageOptions"
      @request="onRequest"
      :selection="selectable ? 'multiple' : 'none'"
      v-model:selected="selected"
      :class="[
        'overview-table',
        {
          'overview-table--virtual col': virtualScroll,
        },
      ]"
      v-bind="$attrs"
    >
      <template v-slot:header="props">
        <q-tr :props="props">
          <q-th
            v-if="selectable"
            class="overview-table__selection"
            :style="`width: ${selectionColumnWidth}px`"
          >
            <q-checkbox v-model="props.selected" :dense="dense" />
          </q-th>

          <q-th
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
            :data-col="col.name"
            :class="[
              col.name === 'action' ? 'text-center' : 'text-left',
              { 'col-highlight': col.name === highlightedCol },
            ]"
            :style="`width: ${headerWidth(col.name)}; position: relative; user-select: none;`"
          >
            <span class="overview-table__label" :title="col.label">{{ col.label }}</span>
            <span
              v-if="isResizable(col.name)"
              class="col-resize-handle"
              @mousedown="startResize($event, col.name)"
              @mouseenter="hoveredHandleCol = col.name"
              @mouseleave="hoveredHandleCol = null"
            />
          </q-th>
        </q-tr>
      </template>

      <template v-slot:loading>
        <q-inner-loading showing color="primary" :transition-duration="100" />
      </template>

      <template v-slot:body="props">
        <q-tr :props="props" :class="{ 'row-highlight': props.row.id === idToDelete }">
          <q-td v-if="selectable" class="overview-table__selection">
            <q-checkbox v-model="props.selected" :dense="dense" />
          </q-td>
          <q-td
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
            :class="[
              ['action', 'created_by'].includes(col.name) ? 'text-center' : 'text-left',
              { 'col-highlight': col.name === highlightedCol },
            ]"
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

      <q-card-section> Are you sure you want to delete this item?</q-card-section>

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
import {
  clampColumnWidth,
  defaultColumnWidths,
  fixedWidthOf,
  hasMaxWidth,
  isColumnResizable,
  maxWidthOf,
  minWidthOf,
  toPixelWidths,
  type ColumnWidths,
  type ColumnWidthValues,
} from '@/utils/overview_table_utils';

const {
  rows,
  loading,
  columns,
  storageKey,
  columnWidths,
  selectable = false,
  dense = false,
  virtualScroll = false,
  tableStyle = '',
  rowKey = 'id',
  rowsPerPageOptions = [0, 10, 25, 50, 100, 200],
} = defineProps<{
  rows: Row[];
  loading: boolean;
  columns: QTableColumn[];
  // prefix of the sessionStorage keys for column widths and visibility
  storageKey: string;
  columnWidths: ColumnWidths;
  selectable?: boolean;
  dense?: boolean;
  virtualScroll?: boolean;
  tableStyle?: string;
  rowsPerPageOptions?: number[];
  rowKey?: string;
}>();

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

  const tableWidth = tableRef.value.$el.querySelector('.q-table__middle')?.clientWidth ?? 0;
  pixelWidths.value = toPixelWidths(
    columnWidths,
    visibleColumnNames.value,
    tableWidth - (selectable ? selectionColumnWidth.value : 0),
  );
  if (!savedColWidths) colWidths.value = defaultColumnWidths(pixelWidths.value);
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

const colWidthsStorageKey = `${storageKey}-col-widths`;
const visibleColumnsStorageKey = `${storageKey}-visible-columns`;

// loading the 'Usersettings'
const savedColWidths = sessionStorage.getItem(colWidthsStorageKey);
// handover the setting
const colWidths = ref<ColumnWidthValues>(
  savedColWidths
    ? Object.fromEntries(
        Object.entries(JSON.parse(savedColWidths)).map(([key, value]) => [key, Number(value)]),
      )
    : {},
);

const pixelWidths = ref<ColumnWidths>({});

// tolerance for floating point comparisons of widths: half a pixel
const WIDTH_EPSILON = 0.5;

// fixed width for checkbox column
const selectionColumnWidth = computed(() => (dense ? 48 : 64));

const visibleColumnNames = computed(() =>
  columns.map((c) => c.name).filter((name) => visibleColumns.value.includes(name)),
);

const isResizable = (colName: string) => isColumnResizable(pixelWidths.value, colName);

const flexibleColumn = computed(() => {
  const candidates = visibleColumnNames.value.filter(isResizable);
  return candidates.filter((c) => !hasMaxWidth(pixelWidths.value, c)).at(-1) ?? candidates.at(-1);
});

function headerWidth(colName: string): string {
  if (!isResizable(colName)) return `${fixedWidthOf(pixelWidths.value, colName)}px`;
  if (colName === flexibleColumn.value) return 'auto';
  return colWidths.value[colName] ? `${colWidths.value[colName]}px` : 'auto';
}

const minTableWidth = computed(() =>
  visibleColumnNames.value.reduce(
    (sum, c) => {
      if (!isResizable(c)) return sum + fixedWidthOf(pixelWidths.value, c);
      if (c === flexibleColumn.value) return sum + minWidthOf(pixelWidths.value, c);
      return sum + (colWidths.value[c] ?? minWidthOf(pixelWidths.value, c));
    },
    selectable ? selectionColumnWidth.value : 0,
  ),
);

const withWidth = (colNames: string[]) => colNames.filter((c) => colWidths.value[c] !== undefined);

const sumWidths = (colNames: string[]) =>
  colNames.reduce((sum, c) => sum + (colWidths.value[c] ?? 0), 0);

const hasRoomToGrow = (colName: string) =>
  colWidths.value[colName]! < maxWidthOf(pixelWidths.value, colName) - WIDTH_EPSILON;

const hasRoomToShrink = (colName: string) =>
  colWidths.value[colName]! > minWidthOf(pixelWidths.value, colName) + WIDTH_EPSILON;

const shrinkableWidth = (colNames: string[]) =>
  withWidth(colNames).reduce(
    (sum, c) => sum + Math.max(0, colWidths.value[c]! - minWidthOf(pixelWidths.value, c)),
    0,
  );

function distributeWidth(amount: number, receivers: string[]) {
  let remaining = amount;
  let candidates = withWidth(receivers).filter(hasRoomToGrow);
  while (remaining > WIDTH_EPSILON && candidates.length > 0) {
    const share = remaining / candidates.length;
    for (const c of candidates) {
      const give = Math.min(share, maxWidthOf(pixelWidths.value, c) - colWidths.value[c]!);
      colWidths.value[c] = colWidths.value[c]! + give;
      remaining -= give;
    }
    candidates = candidates.filter(hasRoomToGrow);
  }
}

function reclaimWidth(amount: number, donors: string[]) {
  let remaining = amount;
  let candidates = withWidth(donors).filter(hasRoomToShrink);
  while (remaining > WIDTH_EPSILON && candidates.length > 0) {
    const share = remaining / candidates.length;
    for (const c of candidates) {
      const take = Math.min(share, colWidths.value[c]! - minWidthOf(pixelWidths.value, c));
      colWidths.value[c] = colWidths.value[c]! - take;
      remaining -= take;
    }
    candidates = candidates.filter(hasRoomToShrink);
  }
}

// functions for setting a new col-widths per mousemove
let resizingCol: string | null = null;
let startX = 0;
let startWidths: ColumnWidthValues = {};
let otherCols: string[] = [];

const hoveredHandleCol = ref<string | null>(null);
const draggedCol = ref<string | null>(null);
const highlightedCol = computed(() => draggedCol.value ?? hoveredHandleCol.value);

function startResize(e: MouseEvent, colName: string) {
  resizingCol = colName;
  draggedCol.value = colName;
  startX = e.clientX;

  const headerRow = (e.target as HTMLElement).closest('tr');
  const ths = headerRow ? Array.from(headerRow.querySelectorAll<HTMLElement>('th[data-col]')) : [];
  const resizableThs = ths.filter((th) => isResizable(th.dataset.col!));
  resizableThs.forEach((th) => {
    colWidths.value[th.dataset.col!] = Math.floor(th.getBoundingClientRect().width);
  });
  startWidths = { ...colWidths.value };
  otherCols = resizableThs.map((th) => th.dataset.col!).filter((c) => c !== colName);

  document.addEventListener('mousemove', onResize);
  document.addEventListener('mouseup', stopResize);
}

function onResize(e: MouseEvent) {
  if (!resizingCol) return;
  colWidths.value = { ...startWidths };
  const startWidth = startWidths[resizingCol] ?? minWidthOf(pixelWidths.value, resizingCol);
  const newWidth = Math.min(
    startWidth + shrinkableWidth(otherCols),
    clampColumnWidth(pixelWidths.value, resizingCol, startWidth + e.clientX - startX),
  );
  colWidths.value[resizingCol] = newWidth;

  const widthDelta = newWidth - startWidth;
  if (widthDelta > 0) {
    reclaimWidth(widthDelta, otherCols);
  } else {
    distributeWidth(-widthDelta, otherCols);
  }
}

function stopResize() {
  const preventSortTrigger = (ev: MouseEvent) => {
    ev.stopPropagation();
    document.removeEventListener('click', preventSortTrigger, true);
  };
  document.addEventListener('click', preventSortTrigger, true);
  resizingCol = null;
  draggedCol.value = null;
  document.removeEventListener('mousemove', onResize);
  document.removeEventListener('mouseup', stopResize);
  sessionStorage.setItem(colWidthsStorageKey, JSON.stringify(colWidths.value));
}

// to select the visibility of the columns
// except actions
const columnOptions = computed(() =>
  columns.filter((c) => c.name !== 'action').map((c) => ({ label: c.label, value: c.name })),
);

const savedColumns = sessionStorage.getItem(visibleColumnsStorageKey);

const visibleColumns = ref<string[]>(
  savedColumns ? JSON.parse(savedColumns) : columns.map((c) => c.name),
);

function setVisibleColumns(newVisibleColumns: string[]) {
  const hidden = visibleColumns.value.filter((c) => !newVisibleColumns.includes(c));
  const shown = newVisibleColumns.filter((c) => !visibleColumns.value.includes(c));
  const remaining = visibleColumns.value.filter(
    (c) => newVisibleColumns.includes(c) && isResizable(c),
  );

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
    setVisibleColumns(columns.map((c) => c.name));
  }
}
</script>

<style>
thead th {
  min-width: 0 !important;
}
</style>
<style scoped>
.overview-table :deep(table.q-table) {
  min-width: var(--overview-table-min-width);
}

.overview-table--fill {
  height: 100%;
}

.overview-table--virtual {
  min-height: 0;
}

.overview-table--virtual :deep(.q-table__middle) {
  flex: 1 1 auto;
  min-height: 0;
}

.overview-table--virtual :deep(thead tr th) {
  position: sticky;
  top: 0;
  z-index: 2;
  background-color: #fff;
}

.row-highlight {
  background-color: rgba(255, 0, 0, 0.1);
}

.overview-table__label {
  display: inline-block;
  width: 0;
  min-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

.overview-table :deep(th.sortable) .overview-table__label {
  min-width: calc(100% - 20px);
}

.overview-table :deep(th .q-table__sort-icon--left),
.overview-table :deep(th .q-table__sort-icon--center) {
  margin-right: calc(-1em - 4px);
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

.overview-table :deep(thead th),
.overview-table :deep(tbody td) {
  transition: background-color 0.3s;
}

.overview-table :deep(th.col-highlight) {
  background-color: #f2f2f2;
}

.overview-table :deep(td.col-highlight) {
  background-color: rgba(0, 0, 0, 0.03);
}

.overview-table .overview-table__selection {
  padding-left: 12px;
  padding-right: 12px;
  text-align: center;
  vertical-align: middle;
}
</style>
