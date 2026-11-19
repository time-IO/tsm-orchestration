<template>
  <q-card class="ingest-option-cluster">
    <q-item class="q-py-md">
      <q-item-section avatar>
        <q-avatar :icon="cluster.icon" color="primary" text-color="white" />
      </q-item-section>
      <q-item-section>
        <q-item-label class="text-h6">{{ cluster.label }}</q-item-label>
        <q-item-label caption>{{ cluster.description }}</q-item-label>
      </q-item-section>
    </q-item>
    <q-separator />

    <q-card-section>
      <div class="row q-col-gutter-md">
        <div v-for="option in cluster.items" :key="option.name" class="col-12 col-md-6 col-lg-12">
          <IngestOptionCard
            v-model:selected-variant="selectedVariant"
            :option="option"
            :variants="variants"
            @help="emit('help', $event)"
            @create="(o, variant) => emit('create', o, variant)"
            @docs="emit('docs', $event)"
          />
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import IngestOptionCard from '@/components/IngestOptionCard.vue';
import type { IngestVariant, IngestCluster, IngestOption } from '@/components/ingestOptions';

withDefaults(
  defineProps<{
    cluster: IngestCluster;
    variants?: IngestVariant[];
  }>(),
  { variants: () => [] },
);

const selectedVariant = defineModel<IngestVariant | null>('selectedVariant', { default: null });

const emit = defineEmits<{
  help: [option: IngestOption];
  create: [option: IngestOption, variant: IngestVariant | null];
  docs: [variant: IngestVariant];
}>();
</script>

<style scoped lang="scss">
@media (min-width: 1440px) {
  .ingest-option-cluster {
    display: grid;
    grid-template-rows: subgrid;
    grid-row: span 3;
  }
}
</style>
