<template>
  <q-input
    v-model="endpointStore.filters.ingest"
    debounce="300"
    outlined
    dense
    clearable
    placeholder="Filter by ingest name..."
    style="max-width: 400px"
  >
    <template #prepend>
      <q-icon name="filter_alt" />
    </template>
  </q-input>
</template>

<script setup lang="ts">
import { useEndpointStore } from '@/stores/endpointStore';

const endpointStore = useEndpointStore();
</script>
