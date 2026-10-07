<template>
  <q-page>
    <div class="q-pa-lg">
      <endpoint-filter class="q-mb-xl" />
      <endpoint-list />
    </div>

    <side-drawer v-model="drawerOpen">
      <endpoint-info
        v-if="endpointStore.selectedEndpoint"
        :endpoint="endpointStore.selectedEndpoint"
        @close="closeDrawer"
      />
      <welcome-text v-else />
    </side-drawer>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import SideDrawer from '@/components/common/SideDrawer.vue';
import EndpointFilter from '@/components/EndpointFilter.vue';
import EndpointInfo from '@/components/EndpointInfo.vue';
import EndpointList from '@/components/EndpointList.vue';
import WelcomeText from '@/components/WelcomeText.vue';
import { useEndpointStore } from '@/stores/endpointStore';

const $q = useQuasar();
const endpointStore = useEndpointStore();

const drawerOpen = ref(false);

onMounted(fetchEndpoints);

watch(() => [endpointStore.filters.q, endpointStore.filters.ingest?.id], fetchEndpoints);

watch(
  () => endpointStore.selectedEndpoint,
  (endpoint) => {
    if (endpoint) drawerOpen.value = true;
  },
);

watch(drawerOpen, (open) => {
  if (!open) endpointStore.selectEndpoint(null);
});

function closeDrawer() {
  drawerOpen.value = false;
}

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
