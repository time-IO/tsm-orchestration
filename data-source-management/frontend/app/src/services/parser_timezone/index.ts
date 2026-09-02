import { axiosInstance } from 'boot/axios';

const apiPath = 'parser_timezone/';

async function getList() {
  return await axiosInstance.get<string[]>(apiPath);
}

export default {
  getList,
};
