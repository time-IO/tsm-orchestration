import type {
  IngestSftpPublic,
  IngestSftpCreate,
  IngestSftpUpdate,
} from 'src/services/ingest_sftp/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = 'ingest/sftp/';

export default createIngestApiService<IngestSftpPublic, IngestSftpCreate, IngestSftpUpdate>(
  apiPath,
);
