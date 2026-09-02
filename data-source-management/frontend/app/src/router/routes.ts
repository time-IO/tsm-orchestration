import type { RouteRecordRaw } from 'vue-router';
import AuthLoginCallback from 'pages/AuthLoginCallback.vue';
import IndexPage from 'pages/IndexPage.vue';
import IngestOverview from 'pages/IngestOverview.vue';
import IngestNew from 'pages/IngestNew.vue';
import IngestNewSftp from 'pages/IngestNewSftp.vue';
import IngestNewMqtt from 'pages/IngestNewMqtt.vue';
import IngestNewExternalSftp from 'pages/IngestNewExternalSftp.vue';
import IngestNewExternalApiBosch from 'pages/IngestNewExternalApiBosch.vue';
import IngestNewExternalApiDwd from 'pages/IngestNewExternalApiDwd.vue';
import IngestNewExternalApiNm from 'pages/IngestNewExternalApiNm.vue';
import IngestNewExternalApiTSystems from 'pages/IngestNewExternalApiTSystems.vue';
import IngestNewExternalApiTtn from 'pages/IngestNewExternalApiTtn.vue';
import IngestNewExternalApiUba from 'pages/IngestNewExternalApiUba.vue';
import IngestDetailExternalApiUba from 'pages/IngestDetailExternalApiUba.vue';
import IngestEditExternalApiUba from 'pages/IngestEditExternalApiUba.vue';
import ParserOverview from 'pages/ParserOverview.vue';
import ParserNew from 'pages/ParserNew.vue';
import ParserNewCsv from 'pages/ParserNewCsv.vue';
import ParserNewJson from 'pages/ParserNewJson.vue';
import QualityControlOverview from 'pages/QualityControlOverview.vue';
import QualityControlNew from 'pages/QualityControlNew.vue';
import IngestDetailExternalApiNm from 'pages/IngestDetailExternalApiNm.vue';
import IngestEditExternalApiNm from 'pages/IngestEditExternalApiNm.vue';
import IngestDetailExternalApiDwd from 'pages/IngestDetailExternalApiDwd.vue';
import IngestEditExternalApiDwd from 'pages/IngestEditExternalApiDwd.vue';
import IngestDetailExternalApiBosch from 'pages/IngestDetailExternalApiBosch.vue';
import IngestEditExternalApiBosch from 'pages/IngestEditExternalApiBosch.vue';
import IngestDetailExternalApiTtn from 'pages/IngestDetailExternalApiTtn.vue';
import IngestEditExternalApiTtn from 'pages/IngestEditExternalApiTtn.vue';
import IngestDetailExternalApiTSystems from 'pages/IngestDetailExternalApiTSystems.vue';
import IngestEditExternalApiTSystems from 'pages/IngestEditExternalApiTSystems.vue';
import IngestDetailMqtt from 'pages/IngestDetailMqtt.vue';
import IngestEditMqtt from 'pages/IngestEditMqtt.vue';
import ParserEditCsv from 'pages/ParserEditCsv.vue';
import ParserEditJson from 'pages/ParserEditJson.vue';
import ParserDetailCsv from 'pages/ParserDetailCsv.vue';
import ParserDetailJson from 'pages/ParserDetailJson.vue';
import IngestDetailSftp from 'pages/IngestDetailSftp.vue';
import IngestEditSftp from 'pages/IngestEditSftp.vue';
import IngestDetailExternalSftp from 'pages/IngestDetailExternalSftp.vue';
import IngestEditExternalSftp from 'pages/IngestEditExternalSftp.vue';
import IngestCopyExternalApiUba from 'pages/IngestCopyExternalApiUba.vue';
import IngestCopyExternalApiBosch from 'pages/IngestCopyExternalApiBosch.vue';
import IngestCopyExternalApiDwd from 'pages/IngestCopyExternalApiDwd.vue';
import IngestCopyExternalApiNm from 'pages/IngestCopyExternalApiNm.vue';
import IngestCopyExternalApiTtn from 'pages/IngestCopyExternalApiTtn.vue';
import IngestCopyExternalApiTSystems from 'pages/IngestCopyExternalApiTSystems.vue';
import IngestCopyExternalApiSensoto from 'pages/IngestCopyExternalApiSensoto.vue';
import IngestDetailExternalApiSensoto from 'pages/IngestDetailExternalApiSensoto.vue';
import IngestEditExternalApiSensoto from 'pages/IngestEditExternalApiSensoto.vue';
import IngestNewExternalApiSensoto from 'pages/IngestNewExternalApiSensoto.vue';
import IngestCopyMqtt from 'pages/IngestCopyMqtt.vue';
import IngestCopySftp from 'pages/IngestCopySftp.vue';
import IngestCopyExternalSftp from 'pages/IngestCopyExternalSftp.vue';
import LegalNotice from 'pages/info/LegalNoticeUfz.vue';
import TermsOfUse from 'pages/info/TermsOfUseUfz.vue';
import ParserCopyCsv from 'pages/ParserCopyCsv.vue';
import ParserCopyJson from 'pages/ParserCopyJson.vue';
import QualityControlDetail from 'pages/QualityControlDetail.vue';
import QualityControlEdit from 'pages/QualityControlEdit.vue';
import QualityControlCopy from 'pages/QualityControlCopy.vue';
import IngestOverviewTriggerExternalApi from 'pages/IngestOverviewTriggerExternalApi.vue';
import ParserNewSoilcan from 'pages/ParserNewSoilcan.vue';
import ParserDetailSoilcan from 'pages/ParserDetailSoilcan.vue';
import ParserEditSoilcan from 'pages/ParserEditSoilcan.vue';
import ParserCopySoilcan from 'pages/ParserCopySoilcan.vue';

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
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/new',
    component: IngestNew,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/new/sftp',
    component: IngestNewSftp,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/new/mqtt',
    component: IngestNewMqtt,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/new/external-sftp',
    component: IngestNewExternalSftp,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/new/external-api/bosch',
    component: IngestNewExternalApiBosch,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/new/external-api/dwd',
    component: IngestNewExternalApiDwd,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/new/external-api/nm',
    component: IngestNewExternalApiNm,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/new/external-api/sensoto',
    component: IngestNewExternalApiSensoto,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/new/external-api/tsystems',
    component: IngestNewExternalApiTSystems,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/new/external-api/ttn',
    component: IngestNewExternalApiTtn,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/new/external-api/uba',
    component: IngestNewExternalApiUba,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/bosch/:id',
    component: IngestDetailExternalApiBosch,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/uba/:id',
    component: IngestDetailExternalApiUba,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/nm/:id',
    component: IngestDetailExternalApiNm,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/ttn/:id',
    component: IngestDetailExternalApiTtn,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/tsystems/:id',
    component: IngestDetailExternalApiTSystems,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/sensoto/:id',
    component: IngestDetailExternalApiSensoto,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/dwd/:id',
    component: IngestDetailExternalApiDwd,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-sftp/:id',
    component: IngestDetailExternalSftp,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/mqtt/:id',
    component: IngestDetailMqtt,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/sftp/:id',
    component: IngestDetailSftp,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/bosch/:id/edit',
    component: IngestEditExternalApiBosch,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/dwd/:id/edit',
    component: IngestEditExternalApiDwd,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/nm/:id/edit',
    component: IngestEditExternalApiNm,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/ttn/:id/edit',
    component: IngestEditExternalApiTtn,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/sensoto/:id/edit',
    component: IngestEditExternalApiSensoto,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-sftp/:id/edit',
    component: IngestEditExternalSftp,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/uba/:id/edit',
    component: IngestEditExternalApiUba,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/tsystems/:id/edit',
    component: IngestEditExternalApiTSystems,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/mqtt/:id/edit',
    component: IngestEditMqtt,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/sftp/:id/edit',
    component: IngestEditSftp,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-sftp/:id/edit',
    component: IngestEditExternalSftp,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/bosch/:id/copy',
    component: IngestCopyExternalApiBosch,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/dwd/:id/copy',
    component: IngestCopyExternalApiDwd,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/nm/:id/copy',
    component: IngestCopyExternalApiNm,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/ttn/:id/copy',
    component: IngestCopyExternalApiTtn,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/tsystems/:id/copy',
    component: IngestCopyExternalApiTSystems,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/uba/:id/copy',
    component: IngestCopyExternalApiUba,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-api/sensoto/:id/copy',
    component: IngestCopyExternalApiSensoto,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/mqtt/:id/copy',
    component: IngestCopyMqtt,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/sftp/:id/copy',
    component: IngestCopySftp,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/ingest/external-sftp/:id/copy',
    component: IngestCopyExternalSftp,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/parser',
    component: ParserOverview,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/parser/new',
    component: ParserNew,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/parser/new/csv',
    component: ParserNewCsv,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/parser/new/json',
    component: ParserNewJson,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/parser/new/soilcan',
    component: ParserNewSoilcan,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/parser/csv/:id',
    component: ParserDetailCsv,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/parser/json/:id',
    component: ParserDetailJson,
    meta: { requiresAuth: true },
  },
  {
    path: '/parser/soilcan/:id',
    component: ParserDetailSoilcan,
    meta: { requiresAuth: true },
  },
  {
    path: '/parser/csv/:id/edit',
    component: ParserEditCsv,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/parser/json/:id/edit',
    component: ParserEditJson,
    meta: { requiresAuth: true },
  },
  {
    path: '/parser/soilcan/:id/edit',
    component: ParserEditSoilcan,
    meta: { requiresAuth: true },
  },
  {
    path: '/parser/csv/:id/copy',
    component: ParserCopyCsv,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/parser/json/:id/copy',
    component: ParserCopyJson,
    meta: { requiresAuth: true },
  },
  {
    path: '/parser/soilcan/:id/copy',
    component: ParserCopySoilcan,
    meta: { requiresAuth: true },
  },
  {
    path: '/quality-control',
    component: QualityControlOverview,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/quality-control/new',
    component: QualityControlNew,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/quality-control/:id',
    component: QualityControlDetail,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/quality-control/:id/edit',
    component: QualityControlEdit,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/quality-control/:id/copy',
    component: QualityControlCopy,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  {
    path: '/info/legal_notice',
    name: 'legal_notice',
    component: LegalNotice,
    meta: { requiresAuth: false, constrainWidth: true },
  },
  {
    path: '/info/terms_of_use',
    name: 'terms_of_use',
    component: TermsOfUse,
    meta: { requiresAuth: false, constrainWidth: true },
  },
  {
    path: '/trigger/external-api',
    component: IngestOverviewTriggerExternalApi,
    meta: { requiresAuth: true, constrainWidth: true },
  },
  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
