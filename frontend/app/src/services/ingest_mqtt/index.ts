import type {
  IngestMqttPublic,
  IngestMqttCreate,
  IngestMqttUpdate,
} from 'src/services/ingest_mqtt/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = 'ingest/mqtt/';

export default createIngestApiService<IngestMqttPublic, IngestMqttCreate, IngestMqttUpdate>(
  apiPath,
);
