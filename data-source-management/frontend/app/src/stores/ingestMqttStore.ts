import { acceptHMRUpdate } from 'pinia';
import type {
  IngestMqttCreate,
  IngestMqttPublic,
  IngestMqttUpdate,
} from 'src/services/ingest_mqtt/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useIngestMqttStore = createIngestStore<
  IngestMqttPublic,
  IngestMqttCreate,
  IngestMqttUpdate
>('ingestMqttStore', API.ingestMqtt);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestMqttStore, import.meta.hot));
}
