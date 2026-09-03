import type {
  IngestExternalMqttPublic,
  IngestExternalMqttCreate,
  IngestExternalMqttUpdate,
} from 'src/services/ingest_external_mqtt/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = 'ingest/external-mqtt/';

export default createIngestApiService<
  IngestExternalMqttPublic,
  IngestExternalMqttCreate,
  IngestExternalMqttUpdate
>(apiPath);
