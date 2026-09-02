import { acceptHMRUpdate } from 'pinia';
import type {
  IngestExternalApiSensotoCreate,
  IngestExternalApiSensotoPublic,
  IngestExternalApiSensotoUpdate,
} from 'src/services/ingest_external_api_sensoto/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useIngestExternalApiSensotoStore = createIngestStore<
  IngestExternalApiSensotoPublic,
  IngestExternalApiSensotoCreate,
  IngestExternalApiSensotoUpdate
>('ingestExternalApiSensotoStore', API.ingestExternalApiSensoto);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiSensotoStore, import.meta.hot));
}
