import { defineStore } from 'pinia';
import { markRaw } from 'vue';
import { defaultPagination } from 'src/utils/pagination_utils';
import type {
  DefaultFilter,
  IngestApiService,
  QTableRequestProp,
  QTableRequestPropPagination,
} from 'src/services/types';

export function createIngestStore<TPublic, TPayloadCreate, TPayloadUpdate>(
  storeId: string,
  apiService: IngestApiService<TPublic, TPayloadCreate, TPayloadUpdate>,
) {
  return defineStore(storeId, {
    state: () => ({
      rows: markRaw([] as TPublic[]),
      pagination: defaultPagination,
      filters: {
        name: undefined,
        uuid: undefined,
        permission_group_id: undefined,
        date_from: undefined,
        date_to: undefined,
        functions: undefined,
      } as DefaultFilter,
      loading: false,
    }),
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
          const response = await apiService.getList(this.pagination, this.filters);
          this.rows = response.data.items;
          this.pagination.rowsPerPage = response.data.size;
          this.pagination.page = response.data.page;
          this.pagination.rowsNumber = response.data.total;
        } finally {
          this.loading = false;
        }
      },
      async dispatchGetOne(id: number): Promise<TPublic> {
        const response = await apiService.getOne(id);
        return response.data;
      },
      async dispatchCreate(payload: TPayloadCreate): Promise<TPublic> {
        const response = await apiService.create(payload);
        return response.data;
      },
      async dispatchUpdate(id: number, payload: TPayloadUpdate): Promise<TPublic> {
        const response = await apiService.update(id, payload);
        return response.data;
      },
      async dispatchDelete(id: number): Promise<void> {
        await apiService.deleteOne(id);
      },
    },
  });
}
