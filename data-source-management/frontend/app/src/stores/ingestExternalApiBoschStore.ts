import { acceptHMRUpdate } from 'pinia';
import type {
  IngestExternalApiBoschCreate,
  IngestExternalApiBoschPublic,
  IngestExternalApiBoschUpdate,
} from 'src/services/ingest_external_api_bosch/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useIngestExternalApiBoschStore = createIngestStore<
  IngestExternalApiBoschPublic,
  IngestExternalApiBoschCreate,
  IngestExternalApiBoschUpdate
>('ingestExternalApiBoschStore', API.ingestExternalApiBosch);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiBoschStore, import.meta.hot));
}
