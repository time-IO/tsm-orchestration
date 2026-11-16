import { axiosInstance } from '@/boot/axios';

const apiPath = 'session/';

async function set() {
  return await axiosInstance.put(apiPath);
}

async function clear() {
  return await axiosInstance.delete(apiPath);
}

export default {
  set,
  clear,
};
