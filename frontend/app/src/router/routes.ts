import type { RouteRecordRaw } from 'vue-router';
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
    component:IndexPage,
  },
  {
    path: '/login-callback',
    component:AuthLoginCallback,
  },
  {
    path: '/silent-renew',
    component:AuthLoginCallback,
  },
  {
    path: '/ingest',
    component: IngestOverviewPage
  },
  {
    path: '/ingest/new',
    component: IngestNewPage
  },
  {
    path: '/ingest/new/sftp',
    component: IngestSftpNewPage
  },
  {
    path: '/ingest/new/mqtt',
    component: IngestMqttNewPage
  },
  {
    path: '/ingest/new/ext-sftp',
    component: IngestExternalSftpNewPage
  },
  {
    path: '/ingest/new/ext-api/bosch',
    component: IngestExternalApiBoschNewPage,
  },
  {
    path: '/ingest/new/ext-api/dwd',
    component: IngestExternalApiDwdNewPage,
  },
  {
    path: '/ingest/new/ext-api/nm',
    component: IngestExternalApiNmNewPage,
  },
  {
    path: '/ingest/new/ext-api/tsystems',
    component: IngestExternalApiTsystemsNewPage,
  },
  {
    path: '/ingest/new/ext-api/ttn',
    component: IngestExternalApiTtnNewPage,
  },
  {
    path: '/ingest/new/ext-api/uba',
    component: IngestExternalApiUbaNewPage,
  },
  {
    path:'/ingest/external-api-uba/:id',
    component: IngestExternalApiUbaDetailPage
  },
  {
    path:'/ingest/external-api-uba/:id/edit',
    component: IngestExternalApiUbaEditPage
  },
  {
    path: '/ingest/:id',
    component: IngestDetailPage
  },
  {
    path: '/ingest/:id/edit',
    component: IngestEditPage
  },
  {
    path: '/parser',
    component: ParserOverviewPage
  },
  {
    path: '/parser/new',
    component: ParserNewPage
  },
  {
    path: '/parser/new/csv',
    component: ParserCsvNewPage
  },
  {
    path: '/quality-control',
    component: QualityControlOverviewPage
  },
  {
    path: '/quality-control/new',
    component: QualityControlNewPage
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
