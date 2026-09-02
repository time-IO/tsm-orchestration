import type {
  IngestExternalApiTSystemsPublic,
  IngestExternalApiTSystemsCreate,
  IngestExternalApiTSystemsUpdate,
} from 'src/services/ingest_external_api_tsystems/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = 'ingest/external-api/tsystems/';

export default createIngestApiService<
  IngestExternalApiTSystemsPublic,
  IngestExternalApiTSystemsCreate,
  IngestExternalApiTSystemsUpdate
>(apiPath);
