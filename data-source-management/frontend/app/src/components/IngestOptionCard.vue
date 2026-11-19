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

    <q-space />
    <q-card-section v-if="option.variantSelect" class="q-pa-sm q-pb-none">
      <q-select
        v-model="selectedVariant"
        :options="filteredVariants"
        option-label="label"
        label="Select API"
        filled
        dense
        clearable
        use-input
        hide-selected
        fill-input
        input-debounce="0"
        @filter="filterVariants"
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
    <q-card-actions>
      <q-btn
        :disable="option.variantSelect && !selectedVariant"
        class="full-width"
        color="green"
        icon="add"
        :label="`Create ${option.variantSelect && selectedVariant ? selectedVariant.label : option.label} ingest`"
        no-caps
        @click="emit('create', option, option.variantSelect ? selectedVariant : null)"
      >
        <q-tooltip v-if="option.variantSelect && !selectedVariant">Select an API first</q-tooltip>
      </q-btn>
    </q-card-actions>
  </q-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { IngestVariant, IngestOption } from '@/components/ingestOptions';

const props = withDefaults(
  defineProps<{
    option: IngestOption;
    /** Variants offered in the dropdown; only used when `option.variantSelect` is set. */
    variants?: IngestVariant[];
  }>(),
  { variants: () => [] },
);

/** The variant chosen in the dropdown (`v-model:selected-variant`). */
const selectedVariant = defineModel<IngestVariant | null>('selectedVariant', { default: null });

const emit = defineEmits<{
  /** The help button was clicked. */
  help: [option: IngestOption];
  /** The create button was clicked; `variant` is the selected variant for ingests with a variant select. */
  create: [option: IngestOption, variant: IngestVariant | null];
  /** The documentation button of a variant in the dropdown was clicked. */
  docs: [variant: IngestVariant];
}>();

const filteredVariants = ref<IngestVariant[]>(props.variants);
watch(
  () => props.variants,
  (variants) => (filteredVariants.value = variants),
);

function filterVariants(input: string, update: (callback: () => void) => void) {
  update(() => {
    const needle = input.trim().toLowerCase();
    filteredVariants.value = needle
      ? props.variants.filter(
          (variant) =>
            variant.label.toLowerCase().includes(needle) || variant.name.includes(needle),
        )
      : props.variants;
  });
}
</script>

<style scoped lang="scss">
.ingest-option-card > * {
  flex-shrink: 0;
}

.ingest-option-card > .q-space {
  flex-shrink: 1;
}
</style>
