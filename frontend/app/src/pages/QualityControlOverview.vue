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

    <trigger-quality-control-settings-dialog
      v-model="showTriggerDialog"
      :ids_to_trigger="selectedIds"
      @success="selection = []"
    />

    <q-table
      ref="tableRef"
      :rows="store.rows"
      :columns="columns"
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
<!--              <q-btn-->
<!--                flat-->
<!--                outline-->
<!--                color="negative"-->
<!--                icon="delete"-->
<!--                @click="setIdToDeleteAndopenDeleteDialog(props.row.id)"-->
<!--              >-->
<!--                <q-tooltip>Delete</q-tooltip>-->
<!--              </q-btn>-->
            </template>

            <template v-else-if="col.name === 'created_by'">
              <q-icon flat class="text-grey-8" name="las la-user-edit" size="sm">
                <q-tooltip>{{ col.value ?? 'N/A'}}</q-tooltip>
              </q-icon>
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
          <q-btn color="negative" flat label="Delete" @click="deleteItem" />
        </q-card-actions>
      </q-card>
    </q-dialog>
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
    required: true,
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
    format: (val) => val?.replace(/^UFZ-TSM:\s*/i, '') ?? '',
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

<style scoped></style>
