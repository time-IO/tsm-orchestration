import type {
  IngestExternalApiDwdPublic,
  IngestExternalApiDwdCreate,
  IngestExternalApiDwdUpdate,
} from 'src/services/ingest_external_api_dwd/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = 'ingest/external-api/dwd/';

export default createIngestApiService<
  IngestExternalApiDwdPublic,
  IngestExternalApiDwdCreate,
  IngestExternalApiDwdUpdate
>(apiPath);
