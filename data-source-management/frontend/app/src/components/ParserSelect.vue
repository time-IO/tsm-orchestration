<template>
  <q-select
    outlined
    v-model="model"
    v-bind="$attrs"
    use-input
    clearable
    :options="filteredOptions"
    @filter="filterOptions"
    virtual-scroll-item-size="72"
    option-value="id"
    option-label="name"
    label="Select the parser *"
    :rules="[rules.REQUIRED]"
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
              color="blue-grey-5"
              text-color="white"
              @click.stop="openParser(scope.opt.id, scope.opt.parser_type)"
            >
              <q-tooltip>Open in new window</q-tooltip>
            </q-icon>
          </q-item-label>

          <q-item-label caption>
            <q-chip dense square color="lime-5" text-color="white">
              {{ scope.opt.parser_type }}
            </q-chip>

            <template v-if="scope.opt.parser_type === 'csv'">
              <q-chip dense square color="teal-5" text-color="white">
                {{ scope.opt.delimiter }}
                <q-tooltip>delimiter</q-tooltip>
              </q-chip>
              <q-chip
                v-for="tc in scope.opt.timestamp_columns ?? []"
                :key="tc.id"
                color="light-green-5"
                text-color="white"
              >
                {{ tc.column }}:{{ tc.timestamp_format }}
                <q-tooltip>timestamp columns</q-tooltip>
              </q-chip>
            </template>

            <template v-if="scope.opt.parser_type === 'json'">
              <q-chip
                v-for="tk in scope.opt.timestamp_keys ?? []"
                :key="tk.id"
                color="light-green-5"
                text-color="white"
              >
                {{ tk.key }}:{{ tk.format }}
                <q-tooltip>timestamp keys</q-tooltip>
              </q-chip>
            </template>

            <template v-if="scope.opt.parser_type === 'soilcan'">
              <q-chip dense square color="teal-5" text-color="white">
                {{ scope.opt.type }}
                <q-tooltip>type</q-tooltip>
              </q-chip>
              <q-chip dense square color="light-green-5" text-color="white">
                {{ scope.opt.header ? 'has header' : 'no header' }}
                <q-tooltip>header</q-tooltip>
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
import type { ParserSelectOption } from 'src/services/types';
import { useQuasar } from 'quasar';
import { useCsvParserStore } from 'stores/parserCsvStore';
import { useJsonParserStore } from 'stores/parserJsonStore';
import { useSoilcanParserStore } from 'stores/parserSoilcanStore';
import { useRouter } from 'vue-router';
import { rules } from 'src/utils/validation/rules';

const csvParserStore = useCsvParserStore();
const jsonParserStore = useJsonParserStore();
const soilcanParserStore = useSoilcanParserStore();
const $q = useQuasar();
const router = useRouter();

const model = defineModel<ParserSelectOption | null | undefined>();
const { preselected_item_id, permission_group_id, parser_type } = defineProps<{
  preselected_item_id?: number | null | undefined;
  permission_group_id: number | null;
  parser_type?: string | null;
}>();

const paginationLoading = ref(false);
const filteredOptions = ref<ParserSelectOption[]>([]);
const isFiltering = ref(false);

/**
 * Maps a parser_type string to its corresponding store.
 * Add new parser types here as they are introduced.
 */
const parserStoresByType: Record<
  string,
  typeof csvParserStore | typeof jsonParserStore | typeof soilcanParserStore
> = {
  csv: csvParserStore,
  json: jsonParserStore,
  soilcan: soilcanParserStore,
};

const parserRowsOfStore = computed<ParserSelectOption[]>(() => {
  if (!parser_type) return [];

  const store = parserStoresByType[parser_type];
  return store ? store.rows.map((row) => ({ ...row, parser_type })) : [];
});

onMounted(async () => {
  if (permission_group_id && parser_type) {
    await fetchOptions();
  }
  /**
   * added extra on mounted, because it didn't fetch the missing item
   * when copy a ingest and directly editing it
   */
  await includeItemIfMissing();
});

async function includeItemIfMissing() {
  if (!preselected_item_id || !parser_type) return;

  const isItemMissing = !parserRowsOfStore.value.some((p) => p.id === preselected_item_id);
  if (!isItemMissing) return;

  const store = parserStoresByType[parser_type];
  if (store) {
    try {
      const item = await store.dispatchGetOne(preselected_item_id);
      filteredOptions.value = [...parserRowsOfStore.value, { ...item, parser_type }];
    } catch {
      $q.notify({
        position: 'top',
        type: 'negative',
        message: 'Failed to fetch single parser',
        timeout: 0,
        actions: [
          {
            icon: 'close',
            color: 'white',
            round: true,
            handler: () => {},
          },
        ],
      });
    }
  } else {
    filteredOptions.value = [...parserRowsOfStore.value];
  }
}

async function fetchOptions() {
  if (!permission_group_id || !parser_type || paginationLoading.value) return;

  paginationLoading.value = true;
  try {
    const store = parserStoresByType[parser_type];
    if (store) {
      store.filters.permission_group_id = permission_group_id;
      store.pagination.rowsPerPage = 250;
      await store.dispatchGetList();
    }
    filteredOptions.value = [...parserRowsOfStore.value];
  } catch {
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch parsers',
      timeout: 0,
      actions: [
        {
          icon: 'close',
          color: 'white',
          round: true,
          handler: () => {},
        },
      ],
    });
  } finally {
    paginationLoading.value = false;
  }
}

function filterOptions(val: string, update: (cb: () => void) => void) {
  if (val === '') {
    update(() => {
      filteredOptions.value = [...parserRowsOfStore.value];
      isFiltering.value = false;
    });
    return;
  }
  update(() => {
    isFiltering.value = true;
    const needle = val.toLowerCase();
    filteredOptions.value = parserRowsOfStore.value.filter((v) =>
      v.name.toLowerCase().includes(needle),
    );
  });
}

const openParser = (id: number, parser_type: string) => {
  const route = router.resolve({
    path: `/parser/${parser_type}/${id}`,
  });
  window.open(route.href, '_blank');
};

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

watch(
  () => parser_type,
  async (newValue) => {
    if (newValue && permission_group_id) {
      await fetchOptions();
    }
  },
);
</script>
