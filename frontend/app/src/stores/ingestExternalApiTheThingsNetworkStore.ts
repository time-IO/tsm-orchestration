import { acceptHMRUpdate } from 'pinia';
import type {
  IngestExternalApiTheThingsNetworkCreate,
  IngestExternalApiTheThingsNetworkPublic,
  IngestExternalApiTheThingsNetworkUpdate,
} from 'src/services/ingest_external_api_the_things_network/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useIngestExternalApiTheThingsNetworkStore = createIngestStore<
  IngestExternalApiTheThingsNetworkPublic,
  IngestExternalApiTheThingsNetworkCreate,
  IngestExternalApiTheThingsNetworkUpdate
>('ingestExternalApiTheThingsNetworkStore', API.ingestExternalApiTheThingsNetwork);

if (import.meta.hot) {
  import.meta.hot.accept(
    acceptHMRUpdate(useIngestExternalApiTheThingsNetworkStore, import.meta.hot),
  );
}
