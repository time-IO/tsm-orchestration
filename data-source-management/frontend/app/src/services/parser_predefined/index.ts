import { axiosInstance } from '@/boot/axios';
import type { PaginatedResponse, ParserRead } from '@/services/types';

const apiPath = 'parser/predefined/';

export function getPredefinedParsers() {
  return axiosInstance.get<PaginatedResponse<ParserRead>>(apiPath, {
    params: { size: 100, recommended_for: 'file' },
  });
}

export function getPredefinedParser(id: number) {
  return axiosInstance.get<ParserRead>(`${apiPath}${id}`);
}
