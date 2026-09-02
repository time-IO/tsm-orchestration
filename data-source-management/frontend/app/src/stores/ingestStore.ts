import { API } from 'src/services';
import { acceptHMRUpdate, defineStore } from 'pinia';
import type {
  IngestFilter,
  QTableRequestProp,
  QTableRequestPropPagination,
} from 'src/services/types';
import { defaultPagination } from 'src/utils/pagination_utils';
import type { IngestWithApiInfoRead } from 'src/services/ingest/types';

export const useIngestStore = defineStore('ingestStore', {
  state: () => ({
    rows: [] as IngestWithApiInfoRead[],
    pagination: defaultPagination,
    filters: {
      name: undefined,
      uuid: undefined,
      ingest_type: undefined,
      permission_group_id: undefined,
      date_from: undefined,
      date_to: undefined,
    } as IngestFilter,
    loading: false,
  }),

  getters: {},

  actions: {
    setPagination(pagination: Partial<QTableRequestPropPagination>) {
      this.pagination = { ...this.pagination, ...pagination };
    },
    resetPage() {
      this.pagination.page = 1;
    },
    async applyFilters() {
      this.resetPage();
      await this.dispatchGetList();
    },
    async onRequest(props: QTableRequestProp) {
      const { page, rowsPerPage, sortBy, descending } = props.pagination;

      this.setPagination({
        page,
        rowsPerPage,
        sortBy,
        descending,
      });

      await this.dispatchGetList();
    },
    async dispatchGetList() {
      try {
        this.loading = true;
        const response = await API.ingest.getList(this.pagination, this.filters);
        this.rows = response.data.items;
        this.pagination.rowsPerPage = response.data.size;
        this.pagination.page = response.data.page;
        this.pagination.rowsNumber = response.data.total;
      } finally {
        this.loading = false;
      }
    },
    async dispatchDelete(id: number): Promise<void> {
      await API.ingest.deleteOne(id);
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestStore, import.meta.hot));
}
