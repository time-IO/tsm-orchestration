import IngestFilter from '@/components/IngestOverviewFilter.vue';

import { describeIngestFilter } from './utils/TestFormSuiteForIngestOverviewFilter';

describeIngestFilter({
  name: 'IngestFilter',
  component: IngestFilter,
  typeModel: 'ingest_type',
  typeSelectName: 'IngestTypeSelect',
  typeValue: 'sftp',
  otherTypeValue: 'mqtt',
  emittedTypeValue: 'http',
});
