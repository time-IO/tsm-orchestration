import { acceptHMRUpdate } from 'pinia';
import type {
  IngestHttpCreate,
  IngestHttpPublic,
  IngestHttpUpdate,
} from 'src/services/ingest_http/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useIngestHttpStore = createIngestStore<
  IngestHttpPublic,
  IngestHttpCreate,
  IngestHttpUpdate
>('ingestHttpStore', API.ingestHttp);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestHttpStore, import.meta.hot));
}
