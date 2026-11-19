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
            v-model:selected-api="selectedApi"
            :option="option"
            :apis="apis"
            @help="emit('help', $event)"
            @create="(o, api) => emit('create', o, api)"
            @docs="emit('docs', $event)"
          />
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import IngestOptionCard from '@/components/IngestOptionCard.vue';
import type { ExternalApi, IngestCluster, IngestOption } from '@/components/ingestOptions';

withDefaults(
  defineProps<{
    cluster: IngestCluster;
    /** APIs offered by API ingests in this cluster. */
    apis?: ExternalApi[];
  }>(),
  { apis: () => [] },
);

/** The API chosen in an API ingest's dropdown (`v-model:selected-api`). */
const selectedApi = defineModel<ExternalApi | null>('selectedApi', { default: null });

const emit = defineEmits<{
  help: [option: IngestOption];
  create: [option: IngestOption, api: ExternalApi | null];
  docs: [api: ExternalApi];
}>();
</script>

<style scoped lang="scss">
// Large screens (Quasar lg, 1440px): the parent lays the clusters out side by side
// in a grid. Each cluster spans three rows (header, separator, content) and shares
// them via subgrid, so all cluster headers have the same height.
@media (min-width: 1440px) {
  .ingest-option-cluster {
    display: grid;
    grid-template-rows: subgrid;
    grid-row: span 3;
  }
}
</style>
