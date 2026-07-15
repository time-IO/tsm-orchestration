import { acceptHMRUpdate } from 'pinia';
import type {
  IngestExternalApiUbaCreate,
  IngestExternalApiUbaPublic,
  IngestExternalApiUbaUpdate,
} from 'src/services/ingest_external_api_uba/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useIngestExternalApiUbaStore = createIngestStore<
  IngestExternalApiUbaPublic,
  IngestExternalApiUbaCreate,
  IngestExternalApiUbaUpdate
>('ingestExternalApiUbaStore', API.ingestExternalApiUba);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiUbaStore, import.meta.hot));
}
