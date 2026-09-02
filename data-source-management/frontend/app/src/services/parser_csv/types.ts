import type { PermissionGroup } from 'src/services/permission_group/types';

export type CsvParserTimestampColumnCreate = {
  column: number | null;
  timestamp_format: string | null;
};
export type CsvParserTimestampColumnUpdate = {
  column: number | null;
  timestamp_format: string | null;
};
export type CsvParserTimestampColumnPublic = {
  id: number;
  column: number;
  timestamp_format: string;
};

export type CsvParserPublic = {
  id: number;
  uuid: string;
  created_by_id: number;
  created_at: string;
  permission_group_id: number;
  name: string;
  description: string | null;
  delimiter: string;
  headlines_to_exclude: string | null;
  footlines_to_exclude: number | null;
  pandas_read_csv: string | null;
  timestamp_columns: Array<CsvParserTimestampColumnPublic>;
  permission_group: PermissionGroup;
  comment: string[];
  header: number | null;
  timezone: string | null;
  encoding: string | null;
};

export type CsvParserCreate = {
  permission_group_id: number | null;
  name: string | null;
  description: string | null;
  delimiter: string | null;
  headlines_to_exclude: string | null;
  footlines_to_exclude: number | null;
  pandas_read_csv: string | null;
  timestamp_columns: Array<CsvParserTimestampColumnCreate>;
  comment: string[];
  header: number | null;
  timezone: string | null;
  encoding: string | null;
};

export type CsvParserUpdate = {
  name?: string | null;
  description?: string | null;
  delimiter?: string | null;
  headlines_to_exclude?: string | null;
  footlines_to_exclude?: number | null;
  pandas_read_csv?: string | null;
  timestamp_columns?: Array<CsvParserTimestampColumnUpdate>;
  header?: number | null;
  comment?: string[];
  timezone?: string | null;
  encoding?: string | null;
};
