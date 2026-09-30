<template>
  <q-input
    v-model="endpointStore.filters.q"
    debounce="300"
    outlined
    dense
    clearable
    placeholder="Search by name..."
    hint="Names are similar to Permission groups"
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
