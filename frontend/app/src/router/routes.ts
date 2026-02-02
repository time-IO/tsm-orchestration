import type {RouteRecordRaw} from 'vue-router';
import IngestNewPage from 'pages/IngestNewPage.vue';
import IngestDetailPage from 'pages/IngestDetailPage.vue';
import IngestEditPage from 'pages/IngestEditPage.vue';
import IngestSftpNewPage from "pages/IngestSftpNewPage.vue";
import IndexPage from 'pages/IndexPage.vue';
import IngestMqttNewPage from 'pages/IngestMqttNewPage.vue';
import IngestExternalSftpNewPage from 'pages/IngestExternalSftpNewPage.vue';
import IngestExternalApiBoschNewPage from "pages/IngestExternalApiBoschNewPage.vue";
import IngestExternalApiDwdNewPage from 'pages/IngestExternalApiDwdNewPage.vue';
import IngestExternalApiNmNewPage from 'pages/IngestExternalApiNmNewPage.vue';
import IngestExternalApiTsystemsNewPage from 'pages/IngestExternalApiTsystemsNewPage.vue';
import IngestExternalApiTtnNewPage from 'pages/IngestExternalApiTtnNewPage.vue';
import IngestExternalApiUbaNewPage from 'pages/IngestExternalApiUbaNewPage.vue';
import IngestExternalApiUbaDetailPage from "pages/IngestExternalApiUbaDetailPage.vue";
import IngestExternalApiUbaEditPage from "pages/IngestExternalApiUbaEditPage.vue";
import ParserCsvNewPage from "pages/ParserCsvNewPage.vue";
import ParserNewPage from "pages/ParserNewPage.vue";
import IngestOverviewPage from "pages/IngestOverviewPage.vue";
import ParserOverviewPage from "pages/ParserOverviewPage.vue";
import QualityControlOverviewPage from "pages/QualityControlOverviewPage.vue";
import QualityControlNewPage from "pages/QualityControlNewPage.vue";
import AuthLoginCallback from "pages/AuthLoginCallback.vue";

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: IndexPage,
    meta: {requiresAuth: false}
  },
  {
    path: '/login-callback',
    component: AuthLoginCallback,
    meta: {requiresAuth: false}
  },
  {
    path: '/silent-renew',
    component: AuthLoginCallback,
    meta: {requiresAuth: false}
  },
  {
    path: '/ingest',
    component: IngestOverviewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/new',
    component: IngestNewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/new/sftp',
    component: IngestSftpNewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/new/mqtt',
    component: IngestMqttNewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/new/ext-sftp',
    component: IngestExternalSftpNewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/new/ext-api/bosch',
    component: IngestExternalApiBoschNewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/new/ext-api/dwd',
    component: IngestExternalApiDwdNewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/new/ext-api/nm',
    component: IngestExternalApiNmNewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/new/ext-api/tsystems',
    component: IngestExternalApiTsystemsNewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/new/ext-api/ttn',
    component: IngestExternalApiTtnNewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/new/ext-api/uba',
    component: IngestExternalApiUbaNewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/external-api-uba/:id',
    component: IngestExternalApiUbaDetailPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/external-api-uba/:id/edit',
    component: IngestExternalApiUbaEditPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/:id',
    component: IngestDetailPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/ingest/:id/edit',
    component: IngestEditPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/parser',
    component: ParserOverviewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/parser/new',
    component: ParserNewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/parser/new/csv',
    component: ParserCsvNewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/quality-control',
    component: QualityControlOverviewPage,
    meta: {requiresAuth: true}
  },
  {
    path: '/quality-control/new',
    component: QualityControlNewPage,
    meta: {requiresAuth: true}
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
