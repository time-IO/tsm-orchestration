import type { RouteRecordRaw } from 'vue-router';
import IndexPage from '@/pages/IndexPage.vue';
import AuthLoginCallback from '@/pages/AuthLoginCallback.vue';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: IndexPage,
    meta: { requiresAuth: false },
  },
  {
    path: '/login-callback',
    component: AuthLoginCallback,
    meta: { requiresAuth: false },
  },
  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('@/pages/ErrorNotFound.vue'),
  },
];

export default routes;
