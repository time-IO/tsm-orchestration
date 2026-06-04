import type { AxiosResponse } from 'axios';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface QTableRequestPropPagination {
  sortBy: string;
  descending: boolean;
  page: number;
  rowsPerPage: number;
  rowsNumber?: number;
}

export interface QTableRequestProp {
  pagination: QTableRequestPropPagination;
}

export type DefaultFilter = {
  name: string | undefined;
  permission_group_id: number | undefined;
  date_from: string | undefined;
  date_to: string | undefined;
  uuid: string | undefined;
};

export type IngestFilter = DefaultFilter & {
  ingest_type: string | undefined;
};

export type IngestExternalApiFilter = DefaultFilter & {
  api_type: string | undefined;
}

export type ParserFilter = DefaultFilter & {
  parser_type: string | undefined;
};

export interface IngestApiService<TPublic, TPayloadCreate, TPayloadUpdate> {
  getList(
    pagination: QTableRequestPropPagination,
    filters: DefaultFilter,
  ): Promise<AxiosResponse<PaginatedResponse<TPublic>>>;
  getOne(id: number): Promise<AxiosResponse<TPublic>>;
  create(payload: TPayloadCreate): Promise<AxiosResponse<TPublic>>;
  update(id: number, payload: TPayloadUpdate): Promise<AxiosResponse<TPublic>>;
  deleteOne(id: number): Promise<AxiosResponse<void>>;
}

export type ParserRead = {
  parser_type: string;
  name: string;
  id: number
}
