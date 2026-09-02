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
    label="API type"
    hint="Select the API type"
  />
</template>

<script setup lang="ts">
import { QSelect } from 'quasar';

const model = defineModel();

const options = [
  { id: 'bosch', name: 'Bosch IoT' },
  { id: 'dwd', name: 'Deutscher Wetterdienst' },
  { id: 'nm', name: 'Neutron Monitor' },
  { id: 'ttn', name: 'The Things network' },
  { id: 'tsystems', name: 'TSystems' },
  { id: 'uba', name: 'Umweltbundesamt (UBA) Air Data' },
  { id: 'sensoto', name: 'Sensoto' },
];
</script>

<style scoped></style>
