import {defineStore, acceptHMRUpdate} from 'pinia';
import type {IngestSftpCreate, IngestSftpPublic, IngestSftpUpdate} from "src/services/ingest_sftp/types";
import {API} from "src/services";

export const useIngestSftpStore = defineStore('ingestSftpStore', {

  state: () => ({
    ingestSftpList: [] as IngestSftpPublic[],
  }),

  getters: {},

  actions: {
    async dispatchGetList() {
      const response = await API.ingestSftp.getList()
      this.ingestSftpList = response.data
    },
    async dispatchGetOne(id: number): Promise<IngestSftpPublic> {
      const response = await API.ingestSftp.getOne(id)
      return response.data

    },
    async dispatchCreate(payload: IngestSftpCreate): Promise<IngestSftpPublic> {
      const response = await API.ingestSftp.create(payload)
      return response.data
    },
    async dispatchUpdate(id: number, payload: IngestSftpUpdate): Promise<IngestSftpPublic> {
      const response = await API.ingestSftp.update(id, payload)
        return response.data
    },
    async dispatchDelete(id: number): Promise<void> {
      await API.ingestSftp.deleteOne(id)
    },
  },
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestSftpStore, import.meta.hot));
}
