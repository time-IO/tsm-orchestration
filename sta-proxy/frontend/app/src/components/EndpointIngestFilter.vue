<template>
  <div>
    <q-select
      v-model="endpointStore.filters.ingest"
      :options="options"
      option-label="name"
      option-value="id"
      use-input
      hide-selected
      fill-input
      input-debounce="300"
      outlined
      dense
      clearable
      :disable="!authStore.isAuthenticated"
      :loading="loading"
      placeholder="Search by ingest..."
      hint="Find and Ingest by its name, ID or UUID"
      @filter="onFilter"
    >
      <template #prepend>
        <q-icon name="input" />
      </template>

      <template #no-option>
        <q-item>
          <q-item-section class="text-grey">No ingests found</q-item-section>
        </q-item>
      </template>
    </q-select>
    <q-tooltip v-if="!authStore.isAuthenticated"> Login to filter by ingest </q-tooltip>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { API } from '@/services';
import type { Ingest } from '@/services/ingests/types';
import { useAuthStore } from '@/stores/authStore';
import { useEndpointStore } from '@/stores/endpointStore';

const $q = useQuasar();
const authStore = useAuthStore();
const endpointStore = useEndpointStore();

const options = ref<Ingest[]>([]);
const loading = ref(false);
let latestRequestId = 0;

async function onFilter(value: string, update: (callback: () => void) => void, abort: () => void) {
  const requestId = ++latestRequestId;
  loading.value = true;
  try {
    const response = await API.ingests.search(value.trim() || undefined);
    if (requestId !== latestRequestId) return;
    update(() => {
      options.value = response.data.items ?? [];
    });
  } catch {
    abort();
    $q.notify({
      position: 'top',
      type: 'negative',
      message: 'Failed to fetch ingests',
    });
  } finally {
    if (requestId === latestRequestId) {
      loading.value = false;
    }
  }
}
</script>
