import type { CsvParserCreate, CsvParserUpdate } from '@/services/parser_csv/types';
import { parseJsonField } from '@/utils/string_utils';

export type CsvParserFormData = Omit<CsvParserCreate, 'pandas_read_csv'> & {
  pandas_read_csv: string | null;
};

export function apiToForm(data: CsvParserCreate): CsvParserFormData {
  return {
    permission_group_id: data.permission_group_id,
    name: data.name || null,
    description: data.description || null,
    delimiter: data.delimiter || null,
    headlines_to_exclude: data.headlines_to_exclude ?? null,
    footlines_to_exclude: data.footlines_to_exclude ?? null,
    pandas_read_csv: data.pandas_read_csv ? JSON.stringify(data.pandas_read_csv, null, 2) : '',
    timestamp_columns: data.timestamp_columns || [],
    comment: [...(data.comment || [])],
    header: data.header ?? null,
    timezone: data.timezone || null,
    encoding: data.encoding || null,
  };
}

export function formToApi(data: CsvParserFormData, includePermissionGroup: true): CsvParserCreate;
export function formToApi(data: CsvParserFormData, includePermissionGroup?: false): CsvParserUpdate;
export function formToApi(
  data: CsvParserFormData,
  includePermissionGroup = false,
): CsvParserCreate | CsvParserUpdate {
  const apiData: Omit<CsvParserCreate, 'permission_group_id'> = {
    name: data.name || null,
    description: data.description || null,
    delimiter: data.delimiter || null,
    headlines_to_exclude: data.headlines_to_exclude ?? null,
    footlines_to_exclude: data.footlines_to_exclude ?? null,
    pandas_read_csv: parseJsonField(data.pandas_read_csv),
    timestamp_columns: data.timestamp_columns || [],
    comment: [...(data.comment || [])],
    header: data.header ?? null,
    timezone: data.timezone || null,
    encoding: data.encoding || null,
  };

  return includePermissionGroup
    ? { ...apiData, permission_group_id: data.permission_group_id }
    : apiData;
}
