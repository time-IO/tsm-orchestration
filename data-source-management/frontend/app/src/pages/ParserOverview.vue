<template>
  <q-page class="q-pa-lg">
    <h5>Overview of Parsers</h5>
    <div class="row q-mb-lg">
      <q-space />
      <q-btn color="green" label="Add Parser" to="/parser/new" />
    </div>
    <parser-overview-filter
      class="q-mt-md q-mb-md"
      v-model:name="store.filters.name"
      v-model:uuid="store.filters.uuid"
      v-model:parser_type="store.filters.parser_type"
      v-model:permission_group_id="store.filters.permission_group_id"
      v-model:date_from="store.filters.date_from"
      v-model:date_to="store.filters.date_to"
      @apply-filters="store.applyFilters"
    />

    <parser-overview-table
      v-model:pagination="pagination"
      :rows="store.rows"
      :loading="store.loading"
      @onRequest="store.onRequest"
      @delete="deleteItem"
    />
  </q-page>
</template>

<script setup lang="ts">
import { computed } from 'vue';
// import IngestOverviewFilter from 'components/IngestOverviewFilter.vue';
import { useQuasar } from 'quasar';
import ParserOverviewTable from 'components/ParserOverviewTable.vue';
import ParserOverviewFilter from 'components/ParserOverviewFilter.vue';
import { useParserDetailedStore } from 'stores/parserDetailedStore';

const $q = useQuasar();

const store = useParserDetailedStore();

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

<style scoped>
.row-highlight {
  background-color: rgba(255, 0, 0, 0.1);
}
</style>
