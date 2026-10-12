import type {
  IngestExternalMqttPublic,
  IngestExternalMqttCreate,
  IngestExternalMqttUpdate,
} from '@/services/ingest_external_mqtt/types';
import { createIngestApiService } from '@/services/factoryIngestService';

const apiPath = 'ingest/external-mqtt/';

export default createIngestApiService<
  IngestExternalMqttPublic,
  IngestExternalMqttCreate,
  IngestExternalMqttUpdate
>(apiPath);
