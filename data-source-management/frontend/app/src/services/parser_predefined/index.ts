import { axiosInstance } from '@/boot/axios';
import type { PaginatedResponse, ParserRead } from '@/services/types';
import { fetchAllPages } from '@/utils/pagination_utils';

const apiPath = 'parser/predefined/';

export type PredefinedParserListParams = {
  page?: number;
  size?: number;
  recommended_for?: 'file' | 'mqtt';
};

async function getList(params: PredefinedParserListParams = {}) {
  return await axiosInstance.get<PaginatedResponse<ParserRead>>(apiPath, { params });
}

async function getOne(id: number) {
  return await axiosInstance.get<ParserRead>(`${apiPath}${id}`);
}

async function getAll(params: Omit<PredefinedParserListParams, 'page' | 'size'> = {}) {
  return await fetchAllPages(async (page, size) => (await getList({ ...params, page, size })).data);
}

export default {
  getList,
  getOne,
  getAll,
};
