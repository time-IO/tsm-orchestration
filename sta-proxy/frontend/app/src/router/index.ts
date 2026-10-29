import { defineRouter } from '#q-app';
import {
  createMemoryHistory,
  createRouter,
  createWebHashHistory,
  createWebHistory,
} from 'vue-router';
import routes from './routes';
import { useAuthStore } from '@/stores/authStore';
import { notifyError } from '@/utils/notify';

export default defineRouter(function (/* { store, ssrContext } */) {
  const createHistory = import.meta.env.QUASAR_SERVER
    ? createMemoryHistory
    : import.meta.env.QUASAR_VUE_ROUTER_MODE === 'history'
      ? createWebHistory
      : createWebHashHistory;

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,
    history: createHistory(import.meta.env.QUASAR_VUE_ROUTER_BASE),
  });

  // Global navigation guard
  Router.beforeEach(async (to) => {
    const authStore = useAuthStore();

    if (!authStore.initialized) {
      await authStore.init();
    }

    // If route requires authentication and user is not authenticated
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
      notifyError('Authentication required! Please login.');

      return '/';
    }
  });

  return Router;
});
