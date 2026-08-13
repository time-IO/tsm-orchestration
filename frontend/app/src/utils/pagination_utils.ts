import type { QTableRequestPropPagination } from 'src/services/types';
import type { QTableColumn } from 'quasar';
import type { IngestWithApiInfoRead } from 'src/services/ingest/types';
import type { ParserDetailedRead } from 'src/services/parser_detailed/types';

export const defaultPagination: QTableRequestPropPagination = {
  sortBy: 'name',
  descending: false,
  page: 1,
  rowsPerPage: 25,
  rowsNumber: 0,
};

export const default_ingest_columns: QTableColumn[] = [
  {
    name: 'id',
    label: 'ID',
    align: 'left',
    field: (row) => row.id,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    name: 'permission_group',
    label: 'Permission Group',
    field: (row) => row.permission_group.name,
    format: (val) => val?.replace(/^[^:]*:\s*/, ''),
    sortable: true,
    align: 'center',
  },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'center' },
  {
    name: 'ingest_type',
    label: 'Type',
    field: 'ingest_type',
    sortable: true,
    align: 'center',
    format: (val) => {
      if (!val) return '';
      switch (val) {
        case 'external_api':
          return 'External API';
        case 'sftp':
          return 'SFTP';
        case 'mqtt':
          return 'MQTT';
        case 'external_sftp':
          return 'External SFTP';
        case 'sensoto':
          return 'Sensoto';
        default:
          return 'Type not defined';
      }
    },
  },
  {
    name: 'created_at',
    label: 'Created at',
    field: 'created_at',
    sortable: true,
    align: 'center',
    format: (val) => {
      if (!val) return '';
      const date = new Date(val);
      const day = String(date.getUTCDate()).padStart(2, '0');
      const month = String(date.getUTCMonth() + 1).padStart(2, '0');
      const year = date.getUTCFullYear();
      return `${day}.${month}.${year}`;
    },
  },
  {
    name: 'created_by',
    label: 'Created by',
    align: 'center',
    field: (row) => row.created_by_username ?? null,
  },

  { name: 'uuid', label: 'UUID', field: 'uuid', align: 'center' },
  { name: 'action', label: 'Actions', align: 'center', field: () => '' },
];
export const default_ingest_external_api_columns: QTableColumn[] = [
  {
    name: 'id',
    label: 'ID',
    align: 'left',
    field: (row) => row.id,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    name: 'permission_group',
    label: 'Permission Group',
    field: (row) => row.permission_group.name,
    format: (val) => val?.replace(/^[^:]*:\s*/, ''),
    sortable: true,
    align: 'center',
  },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'center' },
  {
    name: 'api_type',
    label: 'Type',
    field: 'api_type',
    sortable: true,
    align: 'center',
    format: (val) => {
      if (!val) return '';
      switch (val) {
        case 'bosch':
          return 'Bosch IoT';
        case 'dwd':
          return 'Deutscher Wetterdienst';
        case 'nm':
          return 'Neutron Monitor';
        case 'ttn':
          return 'The Things network';
        case 'tsystems':
          return 'TSystems';
        case 'uba':
          return 'Umweltbundesamt (UBA) Air Data';
        case 'sensoto':
          return 'Sensoto';
        default:
          return '';
      }
    },
  },
  {
    name: 'created_at',
    label: 'Created at',
    field: 'created_at',
    sortable: true,
    align: 'center',
    format: (val) => {
      if (!val) return '';
      const date = new Date(val);
      const day = String(date.getUTCDate()).padStart(2, '0');
      const month = String(date.getUTCMonth() + 1).padStart(2, '0');
      const year = date.getUTCFullYear();
      return `${day}.${month}.${year}`;
    },
  },
  { name: 'uuid', label: 'UUID', field: 'uuid', align: 'center' },
  { name: 'action', label: 'Actions', align: 'center', field: () => '' },
];

export const default_parser_columns: QTableColumn[] = [
  {
    name: 'id',
    label: 'ID',
    align: 'left',
    field: (row) => row.id,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    name: 'permission_group',
    label: 'Permission Group',
    field: (row) => row.permission_group.name,
    format: (val) => val?.replace(/^[^:]*:\s*/, ''),
    sortable: true,
    align: 'center',
  },
  { name: 'name', label: 'Name', field: 'name', sortable: true, align: 'center' },
  {
    name: 'parser_type',
    label: 'Type',
    field: 'parser_type',
    sortable: true,
    align: 'center',
    format: (val: string | null) => {
      if (!val) return '';
      switch (val) {
        case 'csv':
          return 'CSV';
        case 'json':
          return 'JSON';
        case 'soilcan':
          return 'SOILCAN';
        default:
          return 'Type not defined';
      }
    },
  },
  {
    name: 'created_at',
    label: 'Created at',
    field: 'created_at',
    sortable: true,
    align: 'center',
    format: (val) => {
      if (!val) return '';
      const date = new Date(val);
      const day = String(date.getUTCDate()).padStart(2, '0');
      const month = String(date.getUTCMonth() + 1).padStart(2, '0');
      const year = date.getUTCFullYear();
      return `${day}.${month}.${year}`;
    },
  },
  {
    name: 'created_by',
    label: 'Created by',
    align: 'center',
    field: (row) => row.created_by_username ?? null,
  },
  { name: 'uuid', label: 'UUID', align: 'center', field: 'uuid' },

  { name: 'action', label: 'Actions', align: 'center', field: () => '' },
];

export const generateIngestPath = (val: IngestWithApiInfoRead) => {
  if (!val) return '';
  switch (val.ingest_type) {
    case 'external_api':
      switch (val.external_api_type) {
        case 'bosch':
          return `/ingest/external-api/bosch/${val.id}`;
        case 'dwd':
          return `/ingest/external-api/dwd/${val.id}`;
        case 'nm':
          return `/ingest/external-api/nm/${val.id}`;
        case 'ttn':
          return `/ingest/external-api/ttn/${val.id}`;
        case 'tsystems':
          return `/ingest/external-api/tsystems/${val.id}`;
        case 'uba':
          return `/ingest/external-api/uba/${val.id}`;
        case 'sensoto':
          return `/ingest/external-api/sensoto/${val.id}`;

        default:
          return 'api type not defined';
      }
    case 'sftp':
      return `/ingest/sftp/${val.id}`;
    case 'mqtt':
      return `/ingest/mqtt/${val.id}`;
    case 'external_sftp':
      return `/ingest/external-sftp/${val.id}`;
    default:
      return '';
  }
};

export const generateParserPath = (val: ParserDetailedRead) => {
  if (!val) return '';
  switch (val.parser_type) {
    case 'csv':
      return `parser/csv/${val.id}`;
    case 'json':
      return `parser/json/${val.id}`;
    case 'soilcan':
      return `parser/soilcan/${val.id}`;
    default:
      return '';
  }
};

export const formatExternalApiType = (val: string | null) => {
  if (!val) return '';
  switch (val) {
    case 'bosch':
      return 'Bosch IoT';
    case 'dwd':
      return 'Deutscher Wetterdienst';
    case 'nm':
      return 'Neutron Monitor';
    case 'ttn':
      return 'The Things network';
    case 'tsystems':
      return 'TSystems';
    case 'uba':
      return 'Umweltbundesamt (UBA) Air Data';
    case 'sensoto':
      return 'Sensoto';
    default:
      return val;
  }
};
