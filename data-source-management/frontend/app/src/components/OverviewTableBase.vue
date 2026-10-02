<template>
  <div>
    <!-- Icon/Btn: Selecting the Visibility of Columns -->
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
            <!--            select individually-->
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
      :class="{ 'has-selection': hasSelection }"
      :rows="rows"
      :columns="columns"
      :visible-columns="visibleColumns"
      :loading="loading"
      row-key="id"
      flat
      bordered
      v-model:pagination="pagination"
      table-style="table-layout: fixed; width: 100%"
      @request="onRequest"
      v-bind="$attrs"
    >
      <template v-slot:header="tProps">
        <q-tr :props="tProps">
          <q-th v-if="hasSelection" auto-width>
            <q-checkbox
              v-if="$attrs.selection === 'multiple'"
              v-model="tProps.selected"
              :indeterminate-value="null"
            />
          </q-th>
          <q-th
            v-for="col in tProps.cols"
            :key="col.name"
            :props="tProps"
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

      <template v-slot:body="tProps">
        <q-tr :props="tProps">
          <q-td v-if="hasSelection" auto-width>
            <q-checkbox v-model="tProps.selected" />
          </q-td>
          <q-td
            v-for="col in tProps.cols"
            :key="col.name"
            :props="tProps"
            :class="['action', 'created_by'].includes(col.name) ? 'text-center' : 'text-left'"
          >
            <template v-if="col.name === 'action'">
              <slot name="action" :row="tProps.row" />
            </template>

            <template v-else-if="col.name === 'created_by'">
              <q-icon flat class="text-grey-8" name="las la-user-edit" size="sm">
                <q-tooltip>{{ col.value ?? 'N/A' }}</q-tooltip>
              </q-icon>
            </template>

            <template v-else>
              <span
                v-if="col.value !== null && col.value !== undefined && col.value !== ''"
                :style="`display: inline-flex; align-items: center; max-width: ${colWidths[col.name] ? colWidths[col.name] + 'px' : 'auto'}`"
              >
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
                  {{ col.value }}
                  <q-tooltip>
                    {{ cellTooltip ? cellTooltip(col, col.value, tProps.row) : col.value }}
                  </q-tooltip>
                </span>
                <q-btn
                  v-if="col.name === 'uuid'"
                  flat
                  round
                  icon="content_copy"
                  size="xs"
                  text-color="grey"
                  @click="copyClipboard(tProps.row.uuid)"
                >
                  <q-tooltip>Copy UUID</q-tooltip>
                </q-btn>
              </span>
              <span v-else class="text-grey-6">N/A</span>
            </template>
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, useAttrs } from 'vue';
import { copyToClipboard, useQuasar } from 'quasar';
import type { QTableColumn } from 'quasar';
import type { QTableRequestProp, QTableRequestPropPagination } from '@/services/types';

defineOptions({ inheritAttrs: false });

const props = defineProps<{
  rows: unknown[];
  loading: boolean;
  columns: QTableColumn[];
  // prefix for the sessionStorage keys, e.g. 'ingest' -> 'ingest-col-widths'
  storageKey: string;
  cellTooltip?: (col: QTableColumn, value: unknown, row: Record<string, unknown>) => string;
}>();

const pagination = defineModel<QTableRequestPropPagination | undefined>('pagination');
const emit = defineEmits(['onRequest']);
const tableRef = ref();
const attrs = useAttrs();

// selection is passed through via $attrs -> q-table
const hasSelection = computed(() => ['single', 'multiple'].includes(attrs.selection as string));

onMounted(() => {
  // get initial data from server (1st page)
  tableRef.value.requestServerInteraction();
});

function onRequest(p: QTableRequestProp) {
  emit('onRequest', p);
}

const $q = useQuasar();
const copyClipboard = (text: string | null) => {
  if (!text) return;
  copyToClipboard(text)
    .then(() => {
      $q.notify({ message: 'Copied to clipboard', color: 'positive', icon: 'check' });
    })
    .catch(() => {
      $q.notify({ message: 'Failed to copy', color: 'negative', icon: 'error' });
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

const widthsKey = `${props.storageKey}-col-widths`;
const columnsKey = `${props.storageKey}-visible-columns`;

const savedColWidths = sessionStorage.getItem(widthsKey);
const colWidths = ref<Record<string, number>>(
  savedColWidths
    ? Object.fromEntries(
        Object.entries(JSON.parse(savedColWidths)).map(([key, value]) => [key, Number(value)]),
      )
    : defaultColWidths,
);

// column resizing
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
  const min = colMinWidths[resizingCol] ?? 50;
  colWidths.value[resizingCol] = Math.max(min, startWidth + (e.clientX - startX));
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
  sessionStorage.setItem(widthsKey, JSON.stringify(colWidths.value));
}

// column visibility (except 'action')
const columnOptions = computed(() =>
  props.columns.filter((c) => c.name !== 'action').map((c) => ({ label: c.label, value: c.name })),
);

const savedColumns = sessionStorage.getItem(columnsKey);
const visibleColumns = ref<string[]>(
  savedColumns ? JSON.parse(savedColumns) : props.columns.map((c) => c.name),
);

function toggleColumn(colName: string) {
  if (visibleColumns.value.includes(colName)) {
    visibleColumns.value = visibleColumns.value.filter((c) => c !== colName);
  } else {
    visibleColumns.value = [...visibleColumns.value, colName];
  }
  sessionStorage.setItem(columnsKey, JSON.stringify(visibleColumns.value));
}

const allVisible = computed(() =>
  columnOptions.value.every((opt) => visibleColumns.value.includes(opt.value)),
);

function toggleAll() {
  visibleColumns.value = allVisible.value ? ['action'] : props.columns.map((c) => c.name);
  sessionStorage.setItem(columnsKey, JSON.stringify(visibleColumns.value));
}
</script>

<style>
thead th {
  min-width: 0 !important;
}
</style>
<style scoped>
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

/* only needed for the selection checkbox column */
.has-selection th:first-child,
.has-selection td:first-child {
  padding-left: 0;
  padding-right: 0;
  text-align: center;
  vertical-align: middle;
}
</style>
