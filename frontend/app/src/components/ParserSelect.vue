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

    virtual-scroll-item-size="72"
    option-value="id"
    option-label="name"
    label="Select the parser *"
    :rules="[(val) => !!val || 'Parser is required']"
  >
    <template v-slot:hint v-if="!permission_group_id">
      <span class="text-red">Select Permission Group first</span>
    </template>

    <template v-slot:option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section>
          <q-item-label>
            {{ scope.opt.name }}
            <q-icon
              name="launch"
              class="cursor-pointer"
              style="color: grey"
              @click.stop="openParser(scope.opt.id, scope.opt.parser_type)"
            >
              <q-tooltip>Open in new window</q-tooltip>
            </q-icon>
          </q-item-label>

          <q-item-label caption>
            <q-chip dense square color="teal" text-color="white">
              {{ scope.opt.parser_type }}
            </q-chip>

            <template v-if="scope.opt.parser_type === 'csv'">
              <q-chip dense square color="deep-orange-5" text-color="white">
                {{ scope.opt.delimiter }}
                <q-tooltip>delimiter</q-tooltip>
              </q-chip>
              <q-chip
                v-for="tc in scope.opt.timestamp_columns"
                :key="tc.id"
                color="indigo-5"
                text-color="white"
              >
                {{ tc.column }}:{{ tc.timestamp_format }}
                <q-tooltip>timestamp columns</q-tooltip>
              </q-chip>
            </template>

            <template v-if="scope.opt.parser_type === 'json'">
              <q-chip
                v-for="tk in scope.opt.timestamp_keys"
                :key="tk.id"
                color="indigo-5"
                text-color="white"
              >
                {{ tk.key }}:{{ tk.format }}
                <q-tooltip>timestamp keys</q-tooltip>
              </q-chip>
            </template>
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>
    <template v-slot:no-option>
      <q-item>
        <q-item-section class="text-grey">No results</q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue';
import type { CsvParserPublic } from 'src/services/parser_csv/types';
import type { JsonParserPublic } from 'src/services/parser_json/types';
import { useQuasar } from 'quasar';
import { useCsvParserStore } from 'stores/parserCsvStore';
import { useJsonParserStore } from 'stores/parserJsonStore';
import { useRouter } from 'vue-router';

type AnyParser = CsvParserPublic | JsonParserPublic;

const csvParserStore = useCsvParserStore();
const jsonParserStore = useJsonParserStore();
const $q = useQuasar();
const router = useRouter();

const model = defineModel();
const { preselected_item_id, permission_group_id } = defineProps<{
  preselected_item_id?: number | null | undefined;
  permission_group_id: number | null;
}>();

const paginationLoading = ref(false);
const filteredOptions = ref<AnyParser[]>([]);
const isFiltering = ref(false);

const allParsers = computed<AnyParser[]>(() => [...csvParserStore.rows, ...jsonParserStore.rows]);

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
      model.value = null;
    }
    if (newValue != null) {
      await fetchOptions();
    }
  },
);

async function includeItemIfMissing() {
  if (!preselected_item_id) return;

  const isItemMissing = !allParsers.value.some((p) => p.id === preselected_item_id);
  if (isItemMissing) {
    try {
      const item = await csvParserStore.dispatchGetOne(preselected_item_id);
      csvParserStore.rows = [...csvParserStore.rows, item];
    } catch {
      try {
        const item = await jsonParserStore.dispatchGetOne(preselected_item_id);
        jsonParserStore.rows = [...jsonParserStore.rows, item];
      } catch {
        // nicht gefunden
      }
    }
    filteredOptions.value = [...allParsers.value];
  }
}

async function fetchOptions() {
  if (!permission_group_id || paginationLoading.value) return;

  paginationLoading.value = true;
  try {
    csvParserStore.filters.permission_group_id = permission_group_id;
    jsonParserStore.filters.permission_group_id = permission_group_id;
    csvParserStore.pagination.rowsPerPage = 250;
    jsonParserStore.pagination.rowsPerPage = 250;

    await Promise.all([csvParserStore.dispatchGetList(), jsonParserStore.dispatchGetList()]);

    filteredOptions.value = [...allParsers.value];
  } catch {
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch parsers',
    });
  } finally {
    paginationLoading.value = false;
  }
}

function filterOptions(val: string, update: (cb: () => void) => void) {
  if (val === '') {
    update(() => {
      filteredOptions.value = [...allParsers.value];
      isFiltering.value = false;
    });
    return;
  }
  update(() => {
    isFiltering.value = true;
    const needle = val.toLowerCase();
    filteredOptions.value = allParsers.value.filter((v) => v.name.toLowerCase().includes(needle));
  });
}



const openParser = (id: number, parser_type: string) => {
  const route = router.resolve({
    path: `/parser/${parser_type}/${id}`,
  });
  window.open(route.href, '_blank');
};
</script>
