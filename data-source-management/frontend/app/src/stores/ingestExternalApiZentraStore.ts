import { acceptHMRUpdate } from 'pinia';
import type {
  IngestExternalApiZentraCreate,
  IngestExternalApiZentraPublic,
  IngestExternalApiZentraUpdate,
} from '@/services/ingest_external_api_zentra/types';
import { API } from '@/services';
import { createIngestStore } from '@/stores/factoryIngestStore';

export const useIngestExternalApiZentraStore = createIngestStore<
  IngestExternalApiZentraPublic,
  IngestExternalApiZentraCreate,
  IngestExternalApiZentraUpdate
>('ingestExternalApiZentraStore', API.ingestExternalApiZentra);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiZentraStore, import.meta.hot));
}
