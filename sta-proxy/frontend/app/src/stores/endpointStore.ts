import { defineStore } from 'pinia';
import { API } from '@/services';
import type { FrostEndpoint } from '@/services/endpoints/types';

let latestRequestId = 0;

type EndpointFilters = {
  q: string | null;
  ingest: string | null;
};

type EndpointState = {
  endpoints: FrostEndpoint[];
  loading: boolean;
  filters: EndpointFilters;
};

export const useEndpointStore = defineStore('endpoint', {
  state: (): EndpointState => ({
    endpoints: [],
    loading: true,
    filters: {
      q: '',
      ingest: '',
    },
  }),

  actions: {
    async fetchEndpoints() {
      const requestId = ++latestRequestId;
      this.loading = true;
      try {
        const response = await API.endpoints.getList(
          this.filters.q || undefined,
          this.filters.ingest || undefined,
        );
        if (requestId === latestRequestId) {
          this.endpoints = response.data.endpoints ?? [];
        }
      } finally {
        if (requestId === latestRequestId) {
          this.loading = false;
        }
      }
    },
  },
});
