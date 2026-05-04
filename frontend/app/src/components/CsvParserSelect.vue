<template>
  <q-select
    outlined
    v-model="model"
    v-bind="$attrs"
    use-input
    emit-value
    map-options
    clearable
    :options="filteredOptions"
    @filter="filterOptions"
    @virtual-scroll="onVirtualScroll"
    option-value="id"
    option-label="name"
    label="Select the parser *"
    :rules="[(val) => !!val || 'Parser is required']"
  >
    <template v-slot:hint v-if="!permission_group_id">
      <span class="text-red">Select Permission Group first</span>
    </template>
    <template v-slot:option="scope">
      <q-item v-bind="scope.itemProps" clickable>
        <q-item-section>
          <q-item-label>
            {{ scope.opt.name }}
            <q-icon
              name="launch"
              class="cursor-pointer"
              style="color: grey"
              @click="openParser(scope.opt.id)"
            >
              <q-tooltip> Open in new window </q-tooltip>
            </q-icon>
          </q-item-label>
          <q-item-label caption>
            <q-chip dense square color="deep-orange-5" text-color="white">
              {{ scope.opt.delimiter }}
              <q-tooltip> delimiter </q-tooltip>
            </q-chip>
            <q-chip
              v-for="timestampColumn in scope.opt.timestamp_columns"
              :key="timestampColumn.id"
              color="indigo-5"
              text-color="white"
            >
              {{ timestampColumn.column }}:{{ timestampColumn.timestamp_format }}
              <q-tooltip> timestamp columns (index: format) </q-tooltip>
            </q-chip>
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>
    <template v-slot:no-option>
      <q-item>
        <q-item-section class="text-grey"> No results </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup lang="ts">
import { nextTick, ref, watch, computed, onMounted } from 'vue';
import type { CsvParserPublic } from 'src/services/parser_csv/types';
import { useQuasar } from 'quasar';
import { useCsvParserStore } from 'stores/parserCsvStore';
import { useRouter } from 'vue-router';

const csvParserStore = useCsvParserStore();
const $q = useQuasar();
const router = useRouter();

const model = defineModel();
const { preselected_item_id, permission_group_id } = defineProps<{
  preselected_item_id?: number | null | undefined;
  permission_group_id: number | null;
}>();

// Pagination state
const currentPage = ref(1);
const paginationLoading = ref(false);
const allPagesFetched = ref(false);
const accumulatedRows = ref<CsvParserPublic[]>([]);

// Use store rows directly, but maintain local filtered options
const filteredOptions = ref<CsvParserPublic[]>([]);
const isFiltering = ref(false);

// Computed reference to store rows for reactivity
const storeRows = computed(() => csvParserStore.rows as CsvParserPublic[]);

onMounted(async () => {
  /**
   * added extra on mounted, because it didn't fetch the missing item
   * when copy a ingest and directly editing it
   */
  await includeItemIfMissing();
});

watch(
  () => preselected_item_id,
  async (newValue) => {
    if (newValue != null) {
      await includeItemIfMissing();
    }
  },
);

watch(
  () => permission_group_id,
  async (newValue, oldValue) => {
    if (oldValue !== null && oldValue !== newValue) {
      // set parser to null, if an other permission group is selected
      model.value = null;
    }

    if (newValue != null) {
      allPagesFetched.value = false;
      currentPage.value = 1;
      accumulatedRows.value = [];
      await fetchOptions();
    }
  },
);

async function includeItemIfMissing() {
  if (preselected_item_id) {
    const isItemMissing = !storeRows.value.some((option) => option.id === preselected_item_id);
    if (isItemMissing) {
      const preselectedItem = await csvParserStore.dispatchGetOne(preselected_item_id);

      // Add to store directly since we're using its rows
      csvParserStore.rows = [...csvParserStore.rows, preselectedItem];
      filteredOptions.value = [...csvParserStore.rows];
    }
  }
}

async function fetchOptions(page = 1) {
  if (paginationLoading.value || allPagesFetched.value || !permission_group_id) {
    return;
  }

  paginationLoading.value = true;
  try {
    // Set filter and pagination in store state
    csvParserStore.filters.permission_group_id = permission_group_id;
    csvParserStore.pagination.page = page;
    csvParserStore.pagination.rowsPerPage = 50;

    // Use store's dispatchGetList which reads from this.pagination and this.filters
    await csvParserStore.dispatchGetList();

    const newRows = csvParserStore.rows;
    const totalRows = csvParserStore.pagination.rowsNumber || 0;

    // Append new rows to accumulated rows
    if (page === 1) {
      accumulatedRows.value = [...newRows];
    } else {
      // Filter out duplicates by id before appending
      const existingIds = new Set(accumulatedRows.value.map((r) => r.id));
      const uniqueNewRows = newRows.filter((r) => !existingIds.has(r.id));
      accumulatedRows.value = [...accumulatedRows.value, ...uniqueNewRows];
    }

    // Check if we've reached the end by comparing accumulated count to total
    if (accumulatedRows.value.length >= totalRows) {
      allPagesFetched.value = true;
    }

    filteredOptions.value = [...accumulatedRows.value];
    currentPage.value = page + 1;
  } catch {
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch parser',
    });
  } finally {
    paginationLoading.value = false;
  }
}

function filterOptions(val: string, update: (cb: () => void) => void) {
  if (val === '') {
    update(() => {
      filteredOptions.value = [...storeRows.value];
      isFiltering.value = false;
    });
    return;
  }

  update(() => {
    isFiltering.value = true;
    const needle = val.toLowerCase();
    filteredOptions.value = storeRows.value.filter((v) => v.name.toLowerCase().includes(needle));
  });
}

async function onVirtualScroll({ to, ref }: { to: number; ref?: { refresh: () => void } }) {
  const lastIndex = filteredOptions.value.length - 1;

  if (
    !isFiltering.value &&
    !paginationLoading.value &&
    !allPagesFetched.value &&
    to >= lastIndex - 2 // trigger slightly before end for smoother UX
  ) {
    await nextTick(async () => {
      await fetchOptions(currentPage.value);
      await nextTick(() => {
        ref?.refresh(); // Important: refresh virtual list after data update
      });
    });
  }
}

const openParser = (id: number) => {
  if (id) {
    const route = router.resolve({
      path: `/parser/csv/${id}`,
    });

    window.open(route.href, '_blank');
  }
};
</script>

<style scoped></style>
