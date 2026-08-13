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
    label="Parser type"
    hint="Select the parser type"
  />
</template>

<script setup lang="ts">
import { QSelect } from 'quasar';

const model = defineModel();

const options = [
  { id: 'csv', name: 'CSV' },
  { id: 'json', name: 'JSON' },
  { id: 'soilcan', name: 'SOILCAN' },
];
</script>

<style scoped></style>
