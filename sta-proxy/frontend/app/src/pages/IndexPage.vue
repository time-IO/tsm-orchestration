<template>
  <q-page>
    <div class="q-pa-lg">
      <endpoint-filter class="q-mb-xl" />
      <endpoint-list />
    </div>

    <q-drawer
      v-model="drawerOpen"
      side="right"
      show-if-above
      bordered
      :width="500"
      :breakpoint="DRAWER_BREAKPOINT"
    >
      <endpoint-info
        v-if="endpointStore.selectedEndpoint"
        :endpoint="endpointStore.selectedEndpoint"
        @close="closeDrawer"
      />
      <welcome-text v-else />
    </q-drawer>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import EndpointFilter from '@/components/EndpointFilter.vue';
import EndpointInfo from '@/components/EndpointInfo.vue';
import EndpointList from '@/components/EndpointList.vue';
import WelcomeText from '@/components/WelcomeText.vue';
import { useEndpointStore } from '@/stores/endpointStore';

// below this width the drawer is an overlay and not opened initially
const DRAWER_BREAKPOINT = 1024;

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
