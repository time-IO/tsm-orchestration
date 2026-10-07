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
          class="endpoint-row cursor-pointer"
          :class="{
            'endpoint-row--loading': endpointStore.loading,
            'endpoint-row--selected': props.row.name === endpointStore.selectedEndpoint?.name,
          }"
          @click="endpointStore.selectEndpoint(props.row)"
        >
          <q-td key="visibility" :props="props" auto-width>
            <visibility-badge :visibility="endpointVisibility(props.row)" class="full-width" />
          </q-td>

          <q-td key="name" :props="props">
            <div class="text-weight-medium">{{ props.row.display_name }}</div>
            <div class="text-caption text-grey-7">{{ props.row.url }}</div>
          </q-td>

          <q-td key="actions" :props="props" auto-width>
            <copy-button dense :text="props.row.url" />
            <q-btn
              flat
              round
              dense
              icon="open_in_new"
              :href="props.row.url"
              target="_blank"
              rel="noopener noreferrer"
              @click.stop
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
import type { QTableColumn } from 'quasar';
import type { FrostEndpoint } from '@/services/endpoints/types';
import CopyButton from '@/components/common/CopyButton.vue';
import { useEndpointStore } from '@/stores/endpointStore';
import { endpointVisibility } from '@/utils/visibility';
import VisibilityBadge from '@/components/common/VisibilityBadge.vue';

const SKELETON_ROWS = 10;
const SKELETON_DELAY_MS = 1000;

const endpointStore = useEndpointStore();
const columns: QTableColumn<FrostEndpoint>[] = [
  { name: 'visibility', label: 'Visibility', field: 'is_internal', align: 'center' },
  { name: 'name', label: 'Name', field: 'display_name', align: 'left' },
  { name: 'actions', label: 'Actions', field: 'url', align: 'right' },
];

const pagination = ref({ page: 1, rowsPerPage: 25 });

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
</script>

<style scoped>
.endpoint-row {
  transition: opacity 0.2s;
}

.endpoint-row--selected {
  background: rgba(0, 0, 0, 0.06);
}

.endpoint-row--loading {
  opacity: 0.4;
}
</style>
