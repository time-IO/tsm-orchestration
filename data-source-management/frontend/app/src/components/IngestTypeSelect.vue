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
    label="Ingest type"
    hint="Select the Ingest type"
  />
</template>

<script setup lang="ts">
import { QSelect } from 'quasar';

const model = defineModel();

const options = [
  { id: 'mqtt', name: 'Mqtt' },
  { id: 'sftp', name: 'Sftp' },
  { id: 'external_api', name: 'External Api' },
  { id: 'external_sftp', name: 'External Sftp' },
];
</script>

<style scoped></style>
