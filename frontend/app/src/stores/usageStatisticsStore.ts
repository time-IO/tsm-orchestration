import { API } from 'src/services';
import { acceptHMRUpdate, defineStore } from 'pinia';
import type { UsageStatisticsCounts } from 'src/services/usage_statistics/types';

export const useUsageStatisticsStore = defineStore('usageStatisticsStore', {
  state: () => ({
    counts: null as UsageStatisticsCounts | null,
  }),

  getters: {},

  actions: {
    async dispatchGetUsageStatistics() {
      const response = await API.usageStatistics.getUsageStatistics();
      this.counts = response.data.counts;
      return response.data;
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useUsageStatisticsStore, import.meta.hot));
}
