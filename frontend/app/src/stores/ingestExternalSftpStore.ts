import { acceptHMRUpdate } from 'pinia';
import type {
  IngestExternalSftpCreate,
  IngestExternalSftpPublic,
  IngestExternalSftpUpdate,
} from 'src/services/ingest_external_sftp/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useIngestExternalSftpStore = createIngestStore<
  IngestExternalSftpPublic,
  IngestExternalSftpCreate,
  IngestExternalSftpUpdate
>('ingestExternalSftpStore', API.ingestExternalSftp);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalSftpStore, import.meta.hot));
}
