<template>
  <q-page class="q-pa-lg">
    <h5>Overview of Data Ingests</h5>
    <div class="row q-mb-lg">
      <q-space />
      <q-btn color="green" :label="t('newIngest')" to="/ingest/new" />
    </div>
    <ingest-overview-filter
      class="q-mt-md q-mb-md"
      v-model:name="store.filters.name"
      v-model:uuid="store.filters.uuid"
      v-model:ingest_type="store.filters.ingest_type"
      v-model:permission_group_id="store.filters.permission_group_id"
      v-model:date_from="store.filters.date_from"
      v-model:date_to="store.filters.date_to"
      @apply-filters="store.applyFilters"
    />
    <ingest-overview-table
      v-model:pagination="pagination"
      :rows="store.rows"
      :loading="store.loading"
      @onRequest="store.onRequest"
      @delete="deleteItem"
    />
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { computed } from 'vue';
import { useQuasar } from 'quasar';
import { useIngestStore } from 'stores/ingestStore';
import IngestOverviewTable from 'components/IngestOverviewTable.vue';
import IngestOverviewFilter from 'components/IngestOverviewFilter.vue';
const { t } = useI18n();

const $q = useQuasar();

const store = useIngestStore();

const pagination = computed({
  get: () => store.pagination,
  set: (val) => store.setPagination(val),
});

const deleteItem = async (itemId: number | null) => {
  if (!itemId) {
    return;
  }

  try {
    await store.dispatchDelete(itemId);
    $q.notify({
      type: 'positive',
      position: 'top',
      message: 'Item deleted successfully',
    });

    await store.dispatchGetList();
  } catch {
    $q.notify({
      type: 'negative',
      position: 'top',
      message: 'Failed to delete item',
    });
  }
};
</script>

<style scoped></style>
