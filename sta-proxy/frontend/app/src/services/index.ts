import userController from '@/services/user';
import endpointsController from '@/services/endpoints';
import ingestsController from '@/services/ingests';
import sessionController from '@/services/session';

export const API = {
  user: userController,
  endpoints: endpointsController,
  ingests: ingestsController,
  session: sessionController,
};
