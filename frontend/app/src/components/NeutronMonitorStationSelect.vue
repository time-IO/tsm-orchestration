<template>
  <q-select
    outlined
    class="q-mb-md"
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
    option-label="station_id"
    label="Select a station *"
    :rules="[rules.REQUIRED]"
  >
    <template v-slot:option="scope">
      <q-item v-bind="scope.itemProps" clickable>
        <q-item-section>
          <q-item-label>{{ scope.opt.station_id }}</q-item-label>
          <q-item-label caption>{{ scope.opt.description }}</q-item-label>
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
import { nextTick, onMounted, ref, watch } from 'vue';
import type { NeutronMonitorStation } from 'src/services/neutron_monitor_stations/types';
import { useQuasar } from 'quasar';
import { useNeutronMonitorStationStore } from 'stores/neutronMonitorStationStore';
import { rules } from 'src/utils/validation/rules';

const neutronMonitorStationStore = useNeutronMonitorStationStore();

const { preselectedItem } = defineProps<{
  preselectedItem?: NeutronMonitorStation | null | undefined;
}>();

const model = defineModel();

const currentPage = ref(1);
const pageSize = ref(50); // or your desired page size
const paginationTotal = ref(0);
const paginationLoading = ref(false);
const allPagesFetched = ref(false);
const filteredOptions = ref<NeutronMonitorStation[]>([]);
const fetchedOptions = ref<NeutronMonitorStation[]>([]);

const $q = useQuasar();

onMounted(async () => {
  await fetchOptions();
});

watch(
  () => preselectedItem,
  (newValue) => {
    if (newValue != null) {
      includeItemIfMissing();
    }
  },
);

function includeItemIfMissing() {
  if (preselectedItem) {
    const isItemMissing = !fetchedOptions.value.some((option) => option.id === preselectedItem.id);
    if (isItemMissing) {
      fetchedOptions.value = [...fetchedOptions.value, preselectedItem];

      filteredOptions.value = [...fetchedOptions.value];
    }
  }
}

async function fetchOptions(page = 1) {
  if (paginationLoading.value || allPagesFetched.value) return;

  paginationLoading.value = true;
  try {
    const response = await neutronMonitorStationStore.dispatchGetList(page, pageSize.value);
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
      message: 'Failed to fetch stations',
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
      v.station_id.toLowerCase().includes(needle),
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
