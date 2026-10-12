import type {
  IngestSftpPublic,
  IngestSftpCreate,
  IngestSftpUpdate,
} from '@/services/ingest_sftp/types';
import { createIngestApiService } from '@/services/factoryIngestService';

const apiPath = 'ingest/sftp/';

export default createIngestApiService<IngestSftpPublic, IngestSftpCreate, IngestSftpUpdate>(
  apiPath,
);
