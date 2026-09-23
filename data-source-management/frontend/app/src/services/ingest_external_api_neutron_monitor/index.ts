import type {
  IngestExternalApiNeutronMonitorPublic,
  IngestExternalApiNeutronMonitorCreate,
  IngestExternalApiNeutronMonitorUpdate,
} from '@/services/ingest_external_api_neutron_monitor/types';
import { createIngestApiService } from '@/services/factoryIngestService';

const apiPath = 'ingest/external-api/neutron-monitor/';

export default createIngestApiService<
  IngestExternalApiNeutronMonitorPublic,
  IngestExternalApiNeutronMonitorCreate,
  IngestExternalApiNeutronMonitorUpdate
>(apiPath);
