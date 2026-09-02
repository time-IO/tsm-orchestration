import { acceptHMRUpdate } from 'pinia';
import type {
  IngestExternalApiTSystemsCreate,
  IngestExternalApiTSystemsPublic,
  IngestExternalApiTSystemsUpdate,
} from 'src/services/ingest_external_api_tsystems/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useIngestExternalApiTSystemsStore = createIngestStore<
  IngestExternalApiTSystemsPublic,
  IngestExternalApiTSystemsCreate,
  IngestExternalApiTSystemsUpdate
>('ingestExternalApiTSystemsStore', API.ingestExternalApiTSystems);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiTSystemsStore, import.meta.hot));
}
