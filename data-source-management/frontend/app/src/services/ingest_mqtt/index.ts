import type {
  IngestMqttPublic,
  IngestMqttCreate,
  IngestMqttUpdate,
} from '@/services/ingest_mqtt/types';
import { createIngestApiService } from '@/services/factoryIngestService';

const apiPath = 'ingest/mqtt/';

export default createIngestApiService<IngestMqttPublic, IngestMqttCreate, IngestMqttUpdate>(
  apiPath,
);
