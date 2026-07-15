import { axiosInstance } from 'boot/axios';
import type { UserPublic } from 'src/services/user/types';

const apiPath = 'me/';

async function getMe() {
  return await axiosInstance.get<UserPublic>(apiPath);
}

export default {
  getMe,
};
