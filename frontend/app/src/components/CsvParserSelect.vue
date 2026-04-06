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
    <template v-slot:no-option>
      <q-item>
        <q-item-section class="text-grey"> No results </q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup lang="ts">
import { nextTick, ref, watch, computed } from 'vue';
import type { CsvParserPublic } from 'src/services/parser_csv/types';
import { useQuasar } from 'quasar';
import { useCsvParserStore } from 'stores/parserCsvStore';

const csvParserStore = useCsvParserStore();
const $q = useQuasar();

const model = defineModel();
const { preselectedItem, permission_group_id } = defineProps<{
  preselectedItem?: CsvParserPublic | null;
  permission_group_id: number | null;
}>();

// Pagination state
const currentPage = ref(1);
const paginationLoading = ref(false);
const allPagesFetched = ref(false);

// Use store rows directly, but maintain local filtered options
const filteredOptions = ref<CsvParserPublic[]>([]);

// Computed reference to store rows for reactivity
const storeRows = computed(() => csvParserStore.rows as CsvParserPublic[]);

watch(
  () => preselectedItem,
  (newValue) => {
    if (newValue != null) {
      includeStationOfItemIfMissing();
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
      await fetchOptions();
    }
  },
);

function includeStationOfItemIfMissing() {
  if (preselectedItem) {
    const isItemMissing = !storeRows.value.some((option) => option.id === preselectedItem.id);
    if (isItemMissing) {
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

    const rows = csvParserStore.rows;

    // Check if we've reached the end (fewer rows than requested)
    if (
      csvParserStore.pagination.rowsNumber &&
      rows.length >= csvParserStore.pagination.rowsNumber
    ) {
      allPagesFetched.value = true;
    }

    filteredOptions.value = [...rows];
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
    });
    return;
  }

  update(() => {
    const needle = val.toLowerCase();
    filteredOptions.value = storeRows.value.filter((v) => v.name.toLowerCase().includes(needle));
  });
}

async function onVirtualScroll({ to, ref }: { to: number; ref?: { refresh: () => void } }) {
  const lastIndex = filteredOptions.value.length - 1;

  if (
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
</script>

<style scoped></style>
