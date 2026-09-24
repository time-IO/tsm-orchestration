export interface StaEntity {
  name: string;
  '@iot.id': number;
}

export interface BaseDatastream {
  Thing: StaEntity;
  name: string;
}

export interface StaDatastream extends BaseDatastream {
  '@iot.id': number;
  '@iot.selfLink': string;

  Sensor?: StaEntity | null;
  description?: string | null;
  alias?: string | null;
}

export interface StaDatastreamFilters {
  datastream?: string;
  thing?: StaEntity | null;
}

export interface StaDatastreamRequestParameter {
  pagination: QuasarPaginationInterface;
  filters?: StaDatastreamFilters;
}

export interface QuasarPaginationInterface {
  sortBy?: string;
  descending?: boolean;
  page: number;
  rowsPerPage: number;
  rowsNumber: number;
  pages: number;
}
export interface QuasarTableOnRequestInterface {
  sortBy?: string;
  descending?: boolean;
  page?: number;
  rowsPerPage?: number;
  rowsNumber?: number;
  pages?: number;
}

export interface TemporaryDatastream extends BaseDatastream {
  '@iot.id': null;
  '@iot.selfLink': null;
  alias?: string | null;
}

export type Datastream = StaDatastream | TemporaryDatastream;
