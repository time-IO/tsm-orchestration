import {defineStore, acceptHMRUpdate} from 'pinia';
import type {IngestExternalSftpCreate, IngestExternalSftpPublic, IngestExternalSftpUpdate} from "src/services/ingest_external_sftp/types";
import {API} from "src/services";

export const useIngestExternalSftpStore = defineStore('ingestExternalSftpStore', {

  state: () => ({
    ingestExternalSftpList: [] as IngestExternalSftpPublic[],
  }),

  getters: {},

  actions: {
    async dispatchGetList() {
      const response = await API.ingestExternalSftp.getList()
      this.ingestExternalSftpList = response.data
    },
    async dispatchGetOne(id: number): Promise<IngestExternalSftpPublic> {
      const response = await API.ingestExternalSftp.getOne(id)
      return response.data

    },
    async dispatchCreate(payload: IngestExternalSftpCreate): Promise<IngestExternalSftpPublic> {
      const response = await API.ingestExternalSftp.create(payload)
      return response.data
    },
    async dispatchUpdate(id: number, payload: IngestExternalSftpUpdate): Promise<IngestExternalSftpPublic> {
      const response = await API.ingestExternalSftp.update(id, payload)
        return response.data
    },
    async dispatchDelete(id: number): Promise<void> {
      await API.ingestExternalSftp.deleteOne(id)
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalSftpStore, import.meta.hot));
}
