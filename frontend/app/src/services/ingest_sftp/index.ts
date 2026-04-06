import type {
  IngestSftpPublic,
  IngestSftpCreate,
  IngestSftpUpdate,
} from 'src/services/ingest_sftp/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = 'ingest/s3store/';

export default createIngestApiService<IngestSftpPublic, IngestSftpCreate, IngestSftpUpdate>(
  apiPath,
);
