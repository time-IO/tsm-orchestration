<template>
  <div class="q-pa-md">
   <q-input
      v-model="searchQuery"
      debounce="300"
      outlined
      dense
      clearable
      placeholder="Filter endpoints..."
      class="q-mb-md"
      style="max-width: 400px"
   >
    <template #prepend>
      <q-icon name="search" />
    </template>
  </q-input>

    <template v-if="loading">
      <q-item v-for="n in 3" :key="n" style="max-width: 300px">
        <q-item-section avatar>
          <q-skeleton type="QAvatar" />
        </q-item-section>

        <q-item-section>
          <q-item-label>
            <q-skeleton type="text" />
          </q-item-label>
          <q-item-label caption>
            <q-skeleton type="text" width="65%" />
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>

    <template v-else-if="endpoints.length">
      <q-list bordered separator>
        <q-item
          v-for="endpoint in endpoints"
          :key="endpoint.name"
          clickable
          tag="a"
          :href="endpoint.url"
          target="_blank"
          rel="noopener noreferrer"
        >
          <q-item-section avatar>
            <q-icon name="storage" color="primary" />
          </q-item-section>

          <q-item-section>
            <q-item-label>{{ endpoint.displayName }}</q-item-label>
            <q-item-label caption>{{ endpoint.url }}</q-item-label>
          </q-item-section>

          <q-item-section side>
            <q-icon name="launch" />
          </q-item-section>
        </q-item>
      </q-list>
    </template>

    <q-banner v-else class="bg-grey-2"> No FROST endpoints available. </q-banner>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { API } from '@/services';
import type { FrostEndpoint } from '@/services/endpoints/types';

const $q = useQuasar();

const loading = ref(true);
const endpoints = ref<FrostEndpoint[]>([]);
const searchQuery = ref('');


onMounted(async () => {
  await fetchEndpoints();
});

 watch(searchQuery, async () => {
   await fetchEndpoints();
 });

async function fetchEndpoints() {
  loading.value = true;
  try {
      const response = await API.endpoints.getList(searchQuery.value || undefined);
    endpoints.value = response.data.endpoints ?? [];
  } catch {
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch FROST endpoints',
    });
  } finally {
    loading.value = false;
  }
}
</script>
