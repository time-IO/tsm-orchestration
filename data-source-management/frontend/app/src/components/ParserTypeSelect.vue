<template>
  <q-select
    filled
    v-model="model"
    v-bind="$attrs"
    option-value="id"
    option-label="name"
    :options="options"
    clearable
    emit-value
    map-options
    label="Parser type"
    hint="Select the parser type"
  />
</template>

<script setup lang="ts">
import { QSelect } from 'quasar';
import { computed } from 'vue';

const props = defineProps<{ includePredefined?: boolean }>();

const model = defineModel();

const options = computed(() => [
  { id: 'csv', name: 'CSV' },
  { id: 'json', name: 'JSON' },
  { id: 'soilcan', name: 'SOILCAN' },
  ...(props.includePredefined ? [{ id: 'predefined', name: 'Predefined' }] : []),
]);
</script>

<style scoped></style>
