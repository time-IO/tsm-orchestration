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
      :columns="props.columns"
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
          <q-th v-if="$attrs.selection === 'multiple'" auto-width>
            <q-checkbox v-model="props.selected" :indeterminate-value="null" />
          </q-th>
          <q-th
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
            :class="col.name === 'action' ? 'text-center' : 'text-left'"
            :style="`width: ${colWidths[col.name] ?? 'auto'}; position: relative; user-select: none;`"
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
        <q-tr :props="props">
          <q-td v-if="$attrs.selection === 'multiple' || $attrs.selection === 'single'" auto-width>
            <q-checkbox v-model="props.selected" />
          </q-td>
          <q-td v-for="col in props.cols" :key="col.name" :props="props">
            <span v-if="col.value !== null && col.value !== undefined && col.value !== ''">
              <div
                :style="`display: inline-flex; align-items: center; max-width: ${colWidths[col.name] ?? 'auto'}`"
              >
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
                  {{ col.value }}
                  <q-tooltip>{{ col.value }}</q-tooltip>
                </span>
              </div>
            </span>
            <span v-else class="text-grey-6">N/A</span>
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import type { QTableRequestProp, QTableRequestPropPagination } from 'src/services/types';
import { default_ingest_external_api_columns } from 'src/utils/pagination_utils';
import type { QTableColumn } from 'quasar';

defineOptions({
  inheritAttrs: false,
});

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
  },
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

const windowWidth = ref(window.innerWidth);

window.addEventListener('resize', () => {
  windowWidth.value = window.innerWidth;
});

const colMinWidths: Record<string, number> = {
  id: 40,
  permission_group: 40,
  name: 40,
  uuid: 80,
  created_at: 90,
};

const defaultColWidths = ref<Record<string, string>>({
  id: '60px',
  permission_group: windowWidth.value < 1200 ? '80px' : '150px',
  name: windowWidth.value < 1200 ? '80px' : '120px',
  uuid: windowWidth.value < 1200 ? '80px' : '120px',
  created_at: '110px',
});

// loading the 'Usersettings'
const savedColWidths = sessionStorage.getItem('ingestExtApi-col-widths');
// handover the setting
const colWidths = ref<Record<string, string>>(
  savedColWidths ? JSON.parse(savedColWidths) : defaultColWidths.value,
);

// functions for setting a new col-widths
let resizingCol: string | null = null;
let startX = 0;
let startWidth = 0;

function startResize(e: MouseEvent, colName: string) {
  resizingCol = colName;
  startX = e.clientX;

  const th = (e.target as HTMLElement).closest('th');
  startWidth = th ? th.offsetWidth : parseInt(colWidths.value[colName] ?? '100');

  document.addEventListener('mousemove', onResize);
  document.addEventListener('mouseup', stopResize);
}

function onResize(e: MouseEvent) {
  if (!resizingCol) return;
  const diff = e.clientX - startX;
  const min = colMinWidths[resizingCol] ?? 50;
  const newWidth = Math.max(min, startWidth + diff);
  colWidths.value[resizingCol] = newWidth + 'px';
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
  sessionStorage.setItem('ingestExtApi-col-widths', JSON.stringify(colWidths.value));
}

// to select the visibility of the columns
// except actions
const columnOptions = computed(() =>
  default_ingest_external_api_columns
    .filter((c) => c.name !== 'action')
    .map((c) => ({ label: c.label, value: c.name })),
);

const savedColumns = sessionStorage.getItem('ingestExtApi-visible-columns');

const visibleColumns = ref<string[]>(
  savedColumns ? JSON.parse(savedColumns) : default_ingest_external_api_columns.map((c) => c.name),
);

function toggleColumn(colName: string) {
  if (visibleColumns.value.includes(colName)) {
    visibleColumns.value = visibleColumns.value.filter((c) => c !== colName);
  } else {
    visibleColumns.value = [...visibleColumns.value, colName];
  }
  sessionStorage.setItem('ingestExtApi-visible-columns', JSON.stringify(visibleColumns.value));
}

const allVisible = computed(() =>
  columnOptions.value.every((opt) => visibleColumns.value.includes(opt.value)),
);

function toggleAll() {
  if (allVisible.value) {
    visibleColumns.value = ['action'];
  } else {
    visibleColumns.value = default_ingest_external_api_columns.map((c) => c.name);
  }
  sessionStorage.setItem('ingestExtApi-visible-columns', JSON.stringify(visibleColumns.value));
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

.q-table th:first-child,
.q-table td:first-child {
  padding-left: 0;
  padding-right: 0;
  text-align: center;
  vertical-align: middle;
}
</style>
