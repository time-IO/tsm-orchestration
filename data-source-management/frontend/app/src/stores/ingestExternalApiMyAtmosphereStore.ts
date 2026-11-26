import { acceptHMRUpdate } from 'pinia';
import type {
  IngestExternalApiMyAtmosphereCreate,
  IngestExternalApiMyAtmospherePublic,
  IngestExternalApiMyAtmosphereUpdate,
} from '@/services/ingest_external_api_myatmosphere/types';
import { API } from '@/services';
import { createIngestStore } from '@/stores/factoryIngestStore';

export const useIngestExternalApiMyAtmosphereStore = createIngestStore<
  IngestExternalApiMyAtmospherePublic,
  IngestExternalApiMyAtmosphereCreate,
  IngestExternalApiMyAtmosphereUpdate
>('ingestExternalApiMyAtmosphereStore', API.ingestExternalApiMyAtmosphere);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiMyAtmosphereStore, import.meta.hot));
}
