import { acceptHMRUpdate } from 'pinia';
import type {
  IngestExternalMqttCreate,
  IngestExternalMqttPublic,
  IngestExternalMqttUpdate,
} from 'src/services/ingest_external_mqtt/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useIngestExternalMqttStore = createIngestStore<
  IngestExternalMqttPublic,
  IngestExternalMqttCreate,
  IngestExternalMqttUpdate
>('ingestExternalMqttStore', API.ingestExternalMqtt);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalMqttStore, import.meta.hot));
}
