import type {
  IngestExternalSftpPublic,
  IngestExternalSftpCreate,
  IngestExternalSftpUpdate,
} from 'src/services/ingest_external_sftp/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = 'ingest/external-sftp/';

export default createIngestApiService<
  IngestExternalSftpPublic,
  IngestExternalSftpCreate,
  IngestExternalSftpUpdate
>(apiPath);
