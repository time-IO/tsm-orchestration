import { acceptHMRUpdate } from 'pinia';
import type {
  IngestExternalApiDwdCreate,
  IngestExternalApiDwdPublic,
  IngestExternalApiDwdUpdate,
} from 'src/services/ingest_external_api_dwd/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useIngestExternalApiDwdStore = createIngestStore<
  IngestExternalApiDwdPublic,
  IngestExternalApiDwdCreate,
  IngestExternalApiDwdUpdate
>('ingestExternalApiDwdStore', API.ingestExternalApiDwd);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiDwdStore, import.meta.hot));
}
