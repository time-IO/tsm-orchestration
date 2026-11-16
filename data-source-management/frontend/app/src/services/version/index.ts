import { axiosInstance } from '@/boot/axios';
import type { Version } from '@/services/version/types';

const apiPath = 'version/';

async function getVersion() {
  return await axiosInstance.get<Version>(apiPath);
}

export default {
  getVersion,
};
