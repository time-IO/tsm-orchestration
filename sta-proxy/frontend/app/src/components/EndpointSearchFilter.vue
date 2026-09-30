<template>
  <q-input
    v-model="endpointStore.filters.q"
    debounce="300"
    outlined
    dense
    clearable
    placeholder="Filter endpoints..."
    style="max-width: 400px"
  >
    <template #prepend>
      <q-icon name="search" />
    </template>
  </q-input>
</template>

<script setup lang="ts">
import { useEndpointStore } from '@/stores/endpointStore';

const endpointStore = useEndpointStore();
</script>
