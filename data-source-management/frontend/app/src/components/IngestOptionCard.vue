<template>
  <q-card flat bordered class="ingest-option-card full-height column no-wrap">
    <q-item style="min-height: 72px; align-items: center">
      <q-item-section>
        <q-item-label>{{ option.label }}</q-item-label>
        <q-item-label caption>{{ option.description }}</q-item-label>
      </q-item-section>
      <q-item-section side>
        <q-btn
          round
          flat
          icon="help_outline"
          class="text-grey"
          :aria-label="`Help for ${option.label} ingest`"
          @click="emit('help', option)"
        >
          <q-tooltip>When to choose this ingest</q-tooltip>
        </q-btn>
      </q-item-section>
    </q-item>

    <q-card-section v-if="option.apiSelect" class="q-pt-none">
      <q-select
        v-model="selectedApi"
        :options="filteredApis"
        option-label="label"
        label="Select API"
        filled
        dense
        clearable
        use-input
        hide-selected
        fill-input
        input-debounce="0"
        @filter="filterApis"
      >
        <template #prepend>
          <q-icon name="search" />
        </template>
        <template #no-option>
          <q-item>
            <q-item-section class="text-grey">No matching API</q-item-section>
          </q-item>
        </template>
        <template #option="scope">
          <q-item v-bind="scope.itemProps">
            <q-item-section>{{ scope.opt.label }}</q-item-section>
            <q-item-section v-if="scope.opt.docsUrl" side>
              <q-btn
                round
                flat
                dense
                size="sm"
                icon="help_outline"
                class="text-grey"
                :aria-label="`${scope.opt.label} API documentation`"
                @click.stop="emit('docs', scope.opt)"
              >
                <q-tooltip>View API documentation</q-tooltip>
              </q-btn>
            </q-item-section>
          </q-item>
        </template>
      </q-select>
    </q-card-section>

    <q-space />
    <q-separator />
    <q-card-actions>
      <q-btn
        :disable="option.apiSelect && !selectedApi"
        class="full-width"
        color="green"
        icon="add"
        :label="`Create ${option.apiSelect && selectedApi ? selectedApi.label : option.label} ingest`"
        no-caps
        @click="emit('create', option, option.apiSelect ? selectedApi : null)"
      >
        <q-tooltip v-if="option.apiSelect && !selectedApi">Select an API first</q-tooltip>
      </q-btn>
    </q-card-actions>
  </q-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { ExternalApi, IngestOption } from '@/components/ingestOptions';

const props = withDefaults(
  defineProps<{
    option: IngestOption;
    /** APIs offered in the dropdown; only used when `option.apiSelect` is set. */
    apis?: ExternalApi[];
  }>(),
  { apis: () => [] },
);

/** The API chosen in the dropdown (`v-model:selected-api`). */
const selectedApi = defineModel<ExternalApi | null>('selectedApi', { default: null });

const emit = defineEmits<{
  /** The help button was clicked. */
  help: [option: IngestOption];
  /** The create button was clicked; `api` is the selected API for API ingests. */
  create: [option: IngestOption, api: ExternalApi | null];
  /** The documentation button of an API in the dropdown was clicked. */
  docs: [api: ExternalApi];
}>();

const filteredApis = ref<ExternalApi[]>(props.apis);
watch(
  () => props.apis,
  (apis) => (filteredApis.value = apis),
);

function filterApis(input: string, update: (callback: () => void) => void) {
  update(() => {
    const needle = input.trim().toLowerCase();
    filteredApis.value = needle
      ? props.apis.filter(
          (api) => api.label.toLowerCase().includes(needle) || api.name.includes(needle),
        )
      : props.apis;
  });
}
</script>

<style scoped lang="scss">
// Keep every section at its natural height; only the spacer may stretch, so the
// content never gets squeezed into the button below it.
.ingest-option-card > * {
  flex-shrink: 0;
}

.ingest-option-card > .q-space {
  flex-shrink: 1;
}
</style>
