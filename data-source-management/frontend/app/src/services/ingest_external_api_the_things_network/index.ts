import type {
  IngestExternalApiTheThingsNetworkPublic,
  IngestExternalApiTheThingsNetworkCreate,
  IngestExternalApiTheThingsNetworkUpdate,
} from 'src/services/ingest_external_api_the_things_network/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = 'ingest/external-api/the-things-network/';

export default createIngestApiService<
  IngestExternalApiTheThingsNetworkPublic,
  IngestExternalApiTheThingsNetworkCreate,
  IngestExternalApiTheThingsNetworkUpdate
>(apiPath);
