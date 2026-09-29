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

    <qc-setting-overview-table
      v-model:pagination="pagination"
      :rows="store.rows"
      :loading="store.loading"
      selection="multiple"
      v-model:selected="selection"
      @on-request="store.onRequest"
      @delete="setIdToDeleteAndopenDeleteDialog"
    />

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
import { computed, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useQualityControlSettingStore } from '@/stores/qualityControlSettingStore';
import TriggerQualityControlSettingsDialog from '@/components/TriggerQualityControlSettingsDialog.vue';
import QcSettingOverviewFilter from '@/components/QCSettingOverviewFilter.vue';
import QcSettingOverviewTable from '@/components/QcSettingOverviewTable.vue';
import type { QualityControlSettingPublic } from '@/services/quality_control_setting/types';

const { t } = useI18n();
const $q = useQuasar();

const store = useQualityControlSettingStore();
const pagination = computed({
  get: () => store.pagination,
  set: (val) => store.setPagination(val),
});

const deleteDialog = ref(false);
const idToDelete = ref<number | null>(null);

const selection = ref<QualityControlSettingPublic[]>([]);
const selectedIds = computed(() => selection.value.map((item) => item.id));

const showTriggerDialog = ref(false);
const openTriggerDialog = () => {
  showTriggerDialog.value = true;
};

const setIdToDeleteAndopenDeleteDialog = (id: number | null) => {
  idToDelete.value = id;
  deleteDialog.value = true;
};

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
</script>
