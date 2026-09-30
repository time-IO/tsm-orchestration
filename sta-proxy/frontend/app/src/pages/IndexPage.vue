<template>
  <q-page>
    <q-layout view="lHh lpR fFf">
      <div class="q-pa-md">
        <endpoint-search-filter class="q-mb-md" />
        <endpoint-ingest-filter v-if="authStore.isAuthenticated" class="q-mb-md" />
        <endpoint-list />
      </div>
    </q-layout>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue';
import { useQuasar } from 'quasar';
import EndpointIngestFilter from '@/components/EndpointIngestFilter.vue';
import EndpointList from '@/components/EndpointList.vue';
import EndpointSearchFilter from '@/components/EndpointSearchFilter.vue';
import { useAuthStore } from '@/stores/authStore';
import { useEndpointStore } from '@/stores/endpointStore';

const $q = useQuasar();
const authStore = useAuthStore();
const endpointStore = useEndpointStore();

onMounted(fetchEndpoints);

watch(() => ({ ...endpointStore.filters }), fetchEndpoints);

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
