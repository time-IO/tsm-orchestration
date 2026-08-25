import { axiosInstance } from 'boot/axios';
import type { MqttParser } from 'src/services/parser_mqtt/types';
import type { PaginatedResponse } from 'src/services/types';

const apiPath = 'parser/mqtt/';

async function getList(page?: number, size?: number) {
  const params: Record<string, number> = {};
  if (page !== undefined) params.page = page;
  if (size !== undefined) params.size = size;

  return await axiosInstance.get<PaginatedResponse<MqttParser>>(apiPath, {
    params,
  });
}
async function getOne(id: number) {
  return await axiosInstance.get<MqttParser>(`${apiPath}${id}`);
}

export default {
  getList,
  getOne,
};
