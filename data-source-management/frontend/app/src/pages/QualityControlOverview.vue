<template>
  <q-page class="q-pa-lg">
    <h5>Overview of Quality Control Settings</h5>
    <q-card-actions class="q-pa-none">
      <q-space> </q-space>
      <q-btn color="green" :label="t('newSetting')" to="/quality-control/new" />
    </q-card-actions>

    <q-card-actions class="q-pa-none q-mt-md q-mb-lg">
      <q-space> </q-space>
      <q-btn
        :disable="selection.length === 0"
        color="primary"
        label="Trigger"
        @click="openTriggerDialog"
      >
        <q-tooltip
          >Select multiple rows and provide the date range of data that Quality Control Settings
          should be run on</q-tooltip
        >
      </q-btn>
    </q-card-actions>

    <qc-setting-overview-filter
      class="q-mt-md q-mb-md"
      v-model:name="store.filters.name"
      v-model:uuid="store.filters.uuid"
      v-model:permission_group_id="store.filters.permission_group_id"
      v-model:functions="store.filters.functions"
      v-model:date_from="store.filters.date_from"
      v-model:date_to="store.filters.date_to"
      @apply-filters="store.applyFilters"
    />

    <trigger-quality-control-settings-dialog
      v-model="showTriggerDialog"
      :ids_to_trigger="selectedIds"
      @success="selection = []"
    />

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
              <!--              select indiv-->
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
        :rows="store.rows"
        :columns="columns"
        :visible-columns="visibleColumns"
        :loading="store.loading"
        flat
        bordered
        v-model:pagination="pagination"
        @request="store.onRequest"
        selection="multiple"
        v-model:selected="selection"
      >
        <template v-slot:header="props">
          <q-tr :props="props">
            <!-- Selection / Checkbox Header -->
            <q-th auto-width>
              <q-checkbox v-model="props.selected" :indeterminate="props.selected === null" />
            </q-th>

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
            <q-td auto-width>
              <q-checkbox v-model="props.selected" />
            </q-td>
            <q-td
              v-for="col in props.cols"
              :key="col.name"
              :props="props"
              :class="['action', 'created_by'].includes(col.name) ? 'text-center' : 'text-left'"
            >
              <template v-if="col.name === 'action'">
                <q-btn
                  :to="`${basePath}/${props.row.id}`"
                  flat
                  outline
                  color="primary"
                  icon="visibility"
                >
                  <q-tooltip>View details</q-tooltip>
                </q-btn>
                <q-btn
                  :to="`${basePath}/${props.row.id}/edit`"
                  flat
                  outline
                  color="secondary"
                  icon="edit"
                >
                  <q-tooltip>Edit</q-tooltip>
                </q-btn>
                <q-btn
                  :to="`${basePath}/${props.row.id}/copy`"
                  flat
                  outline
                  color="black"
                  icon="content_copy"
                >
                  <q-tooltip>Copy</q-tooltip>
                </q-btn>
                <!--                <q-btn-->
                <!--                  flat-->
                <!--                  outline-->
                <!--                  color="negative"-->
                <!--                  icon="delete"-->
                <!--                  @click="setIdToDeleteAndopenDeleteDialog(props.row.id)"-->
                <!--                >-->
                <!--                  <q-tooltip>Delete</q-tooltip>-->
                <!--                </q-btn>-->
              </template>

              <template v-else-if="col.name === 'created_by'">
                <q-icon flat class="text-grey-8" name="las la-user-edit" size="sm">
                  <q-tooltip>{{ col.value ?? 'N/A' }}</q-tooltip>
                </q-icon>
              </template>

              <template v-else>
                <span v-if="col.value !== null && col.value !== undefined && col.value !== ''">
                  <div
                    :style="`display: inline-flex; align-items: center; max-width: ${colWidths[col.name] ? colWidths[col.name] + 'px' : 'auto'}`"
                  >
                    <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
                      {{ col.value }}
                      <q-tooltip>{{ col.value }}</q-tooltip>
                    </span>
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
            <q-btn color="negative" flat label="Delete" @click="deleteItem" />
          </q-card-actions>
        </q-card>
      </q-dialog>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useQualityControlSettingStore } from 'stores/qualityControlSettingStore';
import type { QTableColumn } from 'quasar';
import { computed, onMounted, ref } from 'vue';
import TriggerQualityControlSettingsDialog from 'components/TriggerQualityControlSettingsDialog.vue';
import type { QualityControlSettingPublic } from 'src/services/quality_control_setting/types';
import { useQuasar } from 'quasar';
import QcSettingOverviewFilter from 'components/QCSettingOverviewFilter.vue';

const { t } = useI18n();
const $q = useQuasar();

const store = useQualityControlSettingStore();
const pagination = computed({
  get: () => store.pagination,
  set: (val) => store.setPagination(val),
});
const tableRef = ref();

const deleteDialog = ref(false);
const idToDelete = ref<number | null>(null);

const selection = ref<QualityControlSettingPublic[]>([]);
const selectedIds = computed(() => {
  return selection.value.map((item) => item.id);
});

const basePath = '/quality-control';

const columns: QTableColumn[] = [
  {
    name: 'id',
    label: 'ID',
    align: 'left',
    field: (row) => row.id,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    name: 'permission_group',
    label: 'Permission Group',
    field: (row) => row.permission_group.name,
    format: (val) => val?.replace(/^[^:]*:\s*/, ''),
    sortable: true,
    align: 'center',
  },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'center' },
  {
    name: 'created_by',
    label: 'Created by',
    align: 'center',
    field: (row) => row.created_by_username ?? null,
  },
  { name: 'action', label: 'Actions', align: 'center', field: () => '' },
];

onMounted(() => {
  tableRef.value.requestServerInteraction();
});

const showTriggerDialog = ref(false);
const openTriggerDialog = () => {
  showTriggerDialog.value = true;
};

// const setIdToDeleteAndopenDeleteDialog = (id: number | null) => {
//   idToDelete.value = id;
//   deleteDialog.value = true;
// };

const deleteItem = async () => {
  if (!idToDelete.value) {
    return;
  }

  try {
    await store.dispatchDelete(idToDelete.value);
    $q.notify({
      type: 'positive',
      message: 'Item deleted successfully',
    });

    await store.dispatchGetList();
    closeDeleteDialog();
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to delete item',
    });
  }
};

const closeDeleteDialog = () => {
  idToDelete.value = null;
  deleteDialog.value = false;
};

const windowWidth = ref(window.innerWidth);

window.addEventListener('resize', () => {
  windowWidth.value = window.innerWidth;
});

const colMinWidths: Record<string, number> = {
  id: 40,
  permission_group: 40,
  name: 40,
  created_by: 60,
  action: 120,
};

const defaultColWidths: Record<string, number> = {
  id: 60,
  permission_group: windowWidth.value < 1200 ? 80 : 150,
  name: windowWidth.value < 1200 ? 80 : 120,
  created_by: 80,
  action: 140,
};

// loading the 'Usersettings'
const savedColWidths = sessionStorage.getItem('qcsetting-col-widths');
// handover the setting
const colWidths = ref<Record<string, number>>(
  savedColWidths
    ? Object.fromEntries(
        Object.entries(JSON.parse(savedColWidths)).map(([key, value]) => [key, Number(value)]),
      )
    : defaultColWidths,
);

// functions for setting a new col-widths per mousemove
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
  colWidths.value[resizingCol] = Math.max(min, startWidth + diff);
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
  sessionStorage.setItem('qcsetting-col-widths', JSON.stringify(colWidths.value));
}

// to select the visibility of the columns
// except actions
const columnOptions = computed(() =>
  columns.filter((c) => c.name !== 'action').map((c) => ({ label: c.label, value: c.name })),
);

const savedColumns = sessionStorage.getItem('qcsetting-visible-columns');

const visibleColumns = ref<string[]>(
  savedColumns ? JSON.parse(savedColumns) : columns.map((c) => c.name),
);

function toggleColumn(colName: string) {
  if (visibleColumns.value.includes(colName)) {
    visibleColumns.value = visibleColumns.value.filter((c) => c !== colName);
  } else {
    visibleColumns.value = [...visibleColumns.value, colName];
  }
  sessionStorage.setItem('qcsetting-visible-columns', JSON.stringify(visibleColumns.value));
}

const allVisible = computed(() =>
  columnOptions.value.every((opt) => visibleColumns.value.includes(opt.value)),
);

function toggleAll() {
  if (allVisible.value) {
    visibleColumns.value = ['action'];
  } else {
    visibleColumns.value = columns.map((c) => c.name);
  }
  sessionStorage.setItem('qcsetting-visible-columns', JSON.stringify(visibleColumns.value));
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
