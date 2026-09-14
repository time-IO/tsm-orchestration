import { acceptHMRUpdate } from 'pinia';
import type {
  IngestExternalApiBoschCreate,
  IngestExternalApiBoschPublic,
  IngestExternalApiBoschUpdate,
} from '@/services/ingest_external_api_bosch/types';
import { API } from '@/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useIngestExternalApiBoschStore = createIngestStore<
  IngestExternalApiBoschPublic,
  IngestExternalApiBoschCreate,
  IngestExternalApiBoschUpdate
>('ingestExternalApiBoschStore', API.ingestExternalApiBosch);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiBoschStore, import.meta.hot));
}
