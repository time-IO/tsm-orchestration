import type {RouteRecordRaw} from 'vue-router';
import AuthLoginCallback from "pages/AuthLoginCallback.vue";
import IndexPage from "pages/IndexPage.vue";
import IngestOverview from "pages/IngestOverview.vue";
import IngestNew from "pages/IngestNew.vue";
import IngestNewSftp from "pages/IngestNewSftp.vue";
import IngestNewMqtt from "pages/IngestNewMqtt.vue";
import IngestNewExternalSftp from "pages/IngestNewExternalSftp.vue";
import IngestNewExternalApiBosch from "pages/IngestNewExternalApiBosch.vue";
import IngestNewExternalApiDwd from "pages/IngestNewExternalApiDwd.vue";
import IngestNewExternalApiNm from "pages/IngestNewExternalApiNm.vue";
import IngestNewExternalApiTSystems from "pages/IngestNewExternalApiTSystems.vue";
import IngestNewExternalApiTtn from "pages/IngestNewExternalApiTtn.vue";
import IngestNewExternalApiUba from "pages/IngestNewExternalApiUba.vue";
import IngestDetailExternalApiUba from "pages/IngestDetailExternalApiUba.vue";
import IngestEditExternalApiUba from "pages/IngestEditExternalApiUba.vue";
import ParserOverview from "pages/ParserOverview.vue";
import ParserNew from "pages/ParserNew.vue";
import ParserNewCsv from "pages/ParserNewCsv.vue";
import QualityControlOverview from "pages/QualityControlOverview.vue";
import QualityControlNew from "pages/QualityControlNew.vue";
import IngestDetailExternalApiNm from "pages/IngestDetailExternalApiNm.vue";
import IngestEditExternalApiNm from 'pages/IngestEditExternalApiNm.vue';
import IngestDetailExternalApiDwd from 'pages/IngestDetailExternalApiDwd.vue';
import IngestEditExternalApiDwd from 'pages/IngestEditExternalApiDwd.vue';
import IngestDetailExternalApiBosch from 'pages/IngestDetailExternalApiBosch.vue';
import IngestEditExternalApiBosch from 'pages/IngestEditExternalApiBosch.vue';
import IngestDetailExternalApiTtn from 'pages/IngestDetailExternalApiTtn.vue';
import IngestEditExternalApiTtn from 'pages/IngestEditExternalApiTtn.vue';
import IngestDetailExternalApiTSystems from 'pages/IngestDetailExternalApiTSystems.vue';
import IngestEditExternalApiTSystems from 'pages/IngestEditExternalApiTSystems.vue';
import IngestDetailMqtt from "pages/IngestDetailMqtt.vue";
import IngestEditMqtt from 'pages/IngestEditMqtt.vue';

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
  {
    path: '/ingest',
    component: IngestOverview,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/new',
    component: IngestNew,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/new/sftp',
    component: IngestNewSftp,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/new/mqtt',
    component: IngestNewMqtt,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/new/ext-sftp',
    component: IngestNewExternalSftp,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/new/ext-api/bosch',
    component: IngestNewExternalApiBosch,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/new/ext-api/dwd',
    component: IngestNewExternalApiDwd,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/new/ext-api/nm',
    component: IngestNewExternalApiNm,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/new/ext-api/tsystems',
    component: IngestNewExternalApiTSystems,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/new/ext-api/ttn',
    component: IngestNewExternalApiTtn,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/new/ext-api/uba',
    component: IngestNewExternalApiUba,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/external-api-bosch/:id',
    component: IngestDetailExternalApiBosch,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/external-api-uba/:id',
    component: IngestDetailExternalApiUba,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/external-api-nm/:id',
    component: IngestDetailExternalApiNm,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/external-api-ttn/:id',
    component: IngestDetailExternalApiTtn,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/external-api-tsystems/:id',
    component: IngestDetailExternalApiTSystems,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/external-api-dwd/:id',
    component: IngestDetailExternalApiDwd,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/mqtt/:id',
    component: IngestDetailMqtt,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/external-api-bosch/:id/edit',
    component: IngestEditExternalApiBosch,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/external-api-dwd/:id/edit',
    component: IngestEditExternalApiDwd,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/external-api-nm/:id/edit',
    component: IngestEditExternalApiNm,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/external-api-ttn/:id/edit',
    component: IngestEditExternalApiTtn,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/external-api-tsystems/:id/edit',
    component: IngestEditExternalApiTSystems,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/external-api-uba/:id/edit',
    component: IngestEditExternalApiUba,
    meta: { requiresAuth: true },
  },
  {
    path: '/ingest/mqtt/:id/edit',
    component: IngestEditMqtt,
    meta: { requiresAuth: true },
  },
  {
    path: '/parser',
    component: ParserOverview,
    meta: { requiresAuth: true },
  },
  {
    path: '/parser/new',
    component: ParserNew,
    meta: { requiresAuth: true },
  },
  {
    path: '/parser/new/csv',
    component: ParserNewCsv,
    meta: { requiresAuth: true },
  },
  {
    path: '/quality-control',
    component: QualityControlOverview,
    meta: { requiresAuth: true },
  },
  {
    path: '/quality-control/new',
    component: QualityControlNew,
    meta: { requiresAuth: true },
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
