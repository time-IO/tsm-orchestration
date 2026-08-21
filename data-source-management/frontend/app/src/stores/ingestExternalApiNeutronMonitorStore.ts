import { acceptHMRUpdate } from 'pinia';
import type {
  IngestExternalApiNeutronMonitorCreate,
  IngestExternalApiNeutronMonitorPublic,
  IngestExternalApiNeutronMonitorUpdate,
} from 'src/services/ingest_external_api_neutron_monitor/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useIngestExternalApiNeutronMonitorStore = createIngestStore<
  IngestExternalApiNeutronMonitorPublic,
  IngestExternalApiNeutronMonitorCreate,
  IngestExternalApiNeutronMonitorUpdate
>('ingestExternalApiUbaStore', API.ingestExternalApiNeutronMonitor);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiNeutronMonitorStore, import.meta.hot));
}
