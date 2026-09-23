import { axiosInstance } from '@/boot/axios';
import type { UserPublic } from '@/services/user/types';

const apiPath = 'me/';

async function getMe() {
  // TODO: getMe endpoint of DSM API used to synch permission groups at the moment, this procedure should be discussed
  return await axiosInstance.get<UserPublic>(apiPath, {
    baseURL: 'http://localhost/data-source-management/api',
  });
}

export default {
  getMe,
};
