<template>
  <q-page>
    <q-layout view="lHh lpR fFf">
      <div class="q-pa-lg">
        <endpoint-filter class="q-mb-xl" />
        <endpoint-list />
      </div>
    </q-layout>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue';
import { useQuasar } from 'quasar';
import EndpointFilter from '@/components/EndpointFilter.vue';
import EndpointList from '@/components/EndpointList.vue';
import { useEndpointStore } from '@/stores/endpointStore';

const $q = useQuasar();
const endpointStore = useEndpointStore();

onMounted(fetchEndpoints);

watch(() => [endpointStore.filters.q, endpointStore.filters.ingest?.id], fetchEndpoints);

async function fetchEndpoints() {
  try {
    await endpointStore.fetchEndpoints();
  } catch {
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch FROST endpoints',
    });
  }
}
</script>

<style scoped></style>
