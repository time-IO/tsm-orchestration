import type {
  IngestExternalSftpPublic,
  IngestExternalSftpCreate,
  IngestExternalSftpUpdate,
} from '@/services/ingest_external_sftp/types';
import { createIngestApiService } from '@/services/factoryIngestService';

const apiPath = 'ingest/external-sftp/';

export default createIngestApiService<
  IngestExternalSftpPublic,
  IngestExternalSftpCreate,
  IngestExternalSftpUpdate
>(apiPath);
