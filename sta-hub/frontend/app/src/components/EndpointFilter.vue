<template>
  <div>
    <div class="text-body1 text-weight-bold q-mb-sm">Filter</div>
    <div class="row q-col-gutter-md">
      <div class="col-12 col-sm-6 col-md-4">
        <endpoint-search-filter />
      </div>

      <div class="col-12 col-sm-6 col-md-4">
        <endpoint-ingest-filter />
      </div>

      <div v-if="endpointStore.hasActiveFilters" class="col-auto">
        <q-btn
          flat
          round
          no-caps
          color="grey"
          icon="filter_alt_off"
          @click="endpointStore.resetFilters()"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import EndpointIngestFilter from '@/components/EndpointIngestFilter.vue';
import EndpointSearchFilter from '@/components/EndpointSearchFilter.vue';
import { useEndpointStore } from '@/stores/endpointStore';

const endpointStore = useEndpointStore();
</script>
