import { defineStore } from 'pinia';
import { API } from '@/services';
import type { FrostEndpoint } from '@/services/endpoints/types';
import type { Ingest } from '@/services/ingests/types';

let latestRequestId = 0;

type EndpointFilters = {
  q: string | null;
  ingest: Ingest | null;
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
      ingest: null,
    },
  }),

  getters: {
    hasActiveFilters: (state) => !!state.filters.q || state.filters.ingest !== null,
  },

  actions: {
    resetFilters() {
      this.filters.q = '';
      this.filters.ingest = null;
    },

    async fetchEndpoints() {
      const requestId = ++latestRequestId;
      this.loading = true;
      try {
        const response = await API.endpoints.getList(
          this.filters.q || undefined,
          this.filters.ingest?.id,
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
