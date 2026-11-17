// test/components/IngestOverviewExternalApiFilter.test.ts
import IngestExternalApiFilter from '@/components/IngestOverviewExternalApiFilter.vue'; // adjust path

import { describeIngestFilter } from './utils/TestFormSuiteForIngestOverviewFilter';

describeIngestFilter({
  name: 'IngestExternalApiFilter',
  component: IngestExternalApiFilter,
  typeModel: 'api_type',
  typeSelectName: 'IngestExternalApiTypeSelect',
  typeValue: 'zentra',
  otherTypeValue: 'other_api',
  emittedTypeValue: 'another_api',
});
