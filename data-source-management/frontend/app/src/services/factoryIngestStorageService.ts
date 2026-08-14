import type { S3ObjectEntry } from 'src/services/ingest_sftp_storage/types';
import { axiosInstance } from 'boot/axios';

export function createIngestStorageService(apiPath: string) {
  async function listFiles(id: number, prefix = '') {
    return await axiosInstance.get<S3ObjectEntry[]>(`${apiPath}${id}/files`, {
      params: { prefix },
    });
  }

  async function downloadFile(id: number, key: string) {
    return await axiosInstance.get<Blob>(`${apiPath}${id}/files/download`, {
      params: { key },
      responseType: 'blob',
    });
  }

  async function uploadFile(id: number, file: File, prefix = '') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('prefix', prefix);
    return await axiosInstance.post<{ ok: boolean; key: string }>(
      `${apiPath}${id}/files/upload`,
      formData,
    );
  }

  async function createDirectory(id: number, name: string, prefix = '') {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('prefix', prefix);
    return await axiosInstance.post<{ ok: boolean; key: string }>(
      `${apiPath}${id}/files/directory`,
      formData,
    );
  }

  return {
    listFiles,
    downloadFile,
    uploadFile,
    createDirectory,
  };
}

export type IngestStorageService = ReturnType<typeof createIngestStorageService>;
