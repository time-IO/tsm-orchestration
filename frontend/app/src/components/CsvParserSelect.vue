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
import { nextTick, ref, watch } from 'vue';
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
const pageSize = ref(50); // or your desired page size
const paginationTotal = ref(0);
const paginationLoading = ref(false);
const allPagesFetched = ref(false);

const filteredOptions = ref<CsvParserPublic[]>([]);
const fetchedOptions = ref<CsvParserPublic[]>([]);

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
    const isItemMissing = !fetchedOptions.value.some((option) => option.id === preselectedItem.id);
    if (isItemMissing) {
      fetchedOptions.value = [...fetchedOptions.value, preselectedItem];

      filteredOptions.value = [...fetchedOptions.value];
    }
  }
}

async function fetchOptions(page = 1) {
  if (paginationLoading.value || allPagesFetched.value || !permission_group_id) {
    return;
  }

  paginationLoading.value = true;
  try {
    const response = await csvParserStore.dispatchGetListbyPermissionGroup(
      permission_group_id,
      page,
      pageSize.value,
    );
    paginationTotal.value = response.total;
    const newItems = response.items;

    // Only add new items if not already included (avoid duplicates)
    const currentIds = new Set(fetchedOptions.value.map((i) => i.id));
    const uniqueNewItems = newItems.filter((item) => !currentIds.has(item.id));
    if (page === 1) {
      fetchedOptions.value = uniqueNewItems;
    } else {
      fetchedOptions.value = [...fetchedOptions.value, ...uniqueNewItems];
    }
    filteredOptions.value = [...fetchedOptions.value];

    // If loaded items < page size, we've reached the end
    if (newItems.length < pageSize.value) {
      allPagesFetched.value = true;
    }
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

// Initial load (page 1)
function filterOptions(val: string, update: (cb: () => void) => void) {
  if (val === '') {
    update(() => {
      filteredOptions.value = [...fetchedOptions.value];
    });
    return;
  }

  // For search, fetch fresh from API with search term if backend supports it,
  // OR do client-side filtering (below), but reset pagination
  update(() => {
    const needle = val.toLowerCase();
    filteredOptions.value = fetchedOptions.value.filter((v) =>
      v.name.toLowerCase().includes(needle),
    );
  });
}

async function onVirtualScroll({ to, ref }: { to: number; ref?: { refresh: () => void } }) {
  const lastIndex = fetchedOptions.value.length - 1;

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
