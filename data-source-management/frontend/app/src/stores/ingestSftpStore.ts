import { acceptHMRUpdate } from 'pinia';
import type {
  IngestSftpCreate,
  IngestSftpPublic,
  IngestSftpUpdate,
} from 'src/services/ingest_sftp/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useIngestSftpStore = createIngestStore<
  IngestSftpPublic,
  IngestSftpCreate,
  IngestSftpUpdate
>('ingestSftpStore', API.ingestSftp);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestSftpStore, import.meta.hot));
}
