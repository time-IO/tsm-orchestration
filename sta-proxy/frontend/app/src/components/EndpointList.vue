<template>
  <div>
    <div class="row items-center q-mb-sm">
      <span class="text-body1 text-weight-bold q-mr-xs">STA Endpoints</span>
      <span class="text-grey-7 text-caption"> ({{ endpointStore.endpoints.length }} found) </span>
    </div>

    <q-table
      v-model:pagination="pagination"
      :rows="endpointStore.endpoints"
      :columns="columns"
      row-key="name"
      :loading="endpointStore.loading"
      :rows-per-page-options="[10, 25, 50, 100, 0]"
      :hide-no-data="endpointStore.loading"
      hide-header
      flat
      bordered
      separator="horizontal"
      no-data-label="No endpoints available."
    >
      <template v-if="showSkeleton" #top-row>
        <q-tr v-for="n in SKELETON_ROWS" :key="`skeleton-${n}`">
          <q-td auto-width class="text-center">
            <q-skeleton type="circle" size="24px" class="q-mx-auto" />
          </q-td>
          <q-td>
            <q-skeleton type="text" width="30%" />
            <q-skeleton type="text" width="55%" class="text-caption" />
          </q-td>
          <q-td auto-width>
            <div class="row no-wrap q-gutter-x-sm">
              <q-skeleton type="circle" size="28px" />
              <q-skeleton type="circle" size="28px" />
            </div>
          </q-td>
        </q-tr>
      </template>

      <template #body="props">
        <q-tr
          :props="props"
          class="endpoint-row"
          :class="{ 'endpoint-row--loading': endpointStore.loading }"
        >
          <q-td key="visibility" :props="props" auto-width>
            <q-icon
              :name="props.row.is_internal ? 'lock_open' : 'visibility'"
              color="primary"
              size="sm"
            >
              <q-tooltip>{{ props.row.is_internal ? 'Internal' : 'Public' }}</q-tooltip>
            </q-icon>
          </q-td>

          <q-td key="name" :props="props">
            <div>{{ props.row.display_name }}</div>
            <div class="text-caption text-grey-7">{{ props.row.url }}</div>
          </q-td>

          <q-td key="actions" :props="props" auto-width>
            <q-btn flat round dense icon="content_copy" @click="copyUrl(props.row.url)">
              <q-tooltip>Copy URI</q-tooltip>
            </q-btn>
            <q-btn
              flat
              round
              dense
              icon="open_in_new"
              :href="props.row.url"
              target="_blank"
              rel="noopener noreferrer"
            >
              <q-tooltip>Open in new tab</q-tooltip>
            </q-btn>
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue';
import { copyToClipboard, useQuasar } from 'quasar';
import type { QTableColumn } from 'quasar';
import type { FrostEndpoint } from '@/services/endpoints/types';
import { useEndpointStore } from '@/stores/endpointStore';

const SKELETON_ROWS = 10;
const SKELETON_DELAY_MS = 1000;

const $q = useQuasar();
const endpointStore = useEndpointStore();

const columns: QTableColumn<FrostEndpoint>[] = [
  { name: 'visibility', label: 'Visibility', field: 'is_internal', align: 'center' },
  { name: 'name', label: 'Name', field: 'display_name', align: 'left' },
  { name: 'actions', label: 'Actions', field: 'url', align: 'right' },
];

const pagination = ref({ page: 1, rowsPerPage: 25 });

// The skeleton is only shown for the initial load, and only if it takes
// longer than SKELETON_DELAY_MS. Later refreshes grey out the current rows.
const showSkeleton = ref(false);
let skeletonTimer: ReturnType<typeof setTimeout> | undefined;

function clearSkeletonTimer() {
  clearTimeout(skeletonTimer);
  skeletonTimer = undefined;
}

watch(
  () => endpointStore.loading,
  (loading, wasLoading) => {
    const isInitialLoad = wasLoading === undefined && endpointStore.endpoints.length === 0;
    if (loading && isInitialLoad) {
      skeletonTimer = setTimeout(() => {
        showSkeleton.value = endpointStore.loading;
      }, SKELETON_DELAY_MS);
    } else if (!loading) {
      clearSkeletonTimer();
      showSkeleton.value = false;
    }
  },
  { immediate: true },
);

onBeforeUnmount(clearSkeletonTimer);

async function copyUrl(url: string) {
  try {
    await copyToClipboard(url);
    $q.notify({ position: 'top', type: 'positive', message: 'URI copied to clipboard' });
  } catch {
    $q.notify({ position: 'top', type: 'negative', message: 'Failed to copy URI' });
  }
}
</script>

<style scoped>
.endpoint-row {
  transition: opacity 0.2s;
}

.endpoint-row--loading {
  opacity: 0.4;
}
</style>
