import { describe, expect, it } from 'vitest';
import type { CsvParserCreate } from '@/services/parser_csv/types';
import { apiToForm, formToApi, type CsvParserFormData } from '@/utils/parser_csv_utils';

const apiData: CsvParserCreate = {
  permission_group_id: 12,
  name: 'Parser',
  description: null,
  delimiter: ',',
  headlines_to_exclude: null,
  footlines_to_exclude: 0,
  pandas_read_csv: { na_values: ['-', 'NA'] },
  timestamp_columns: [{ column: 0, timestamp_format: '%Y-%m-%d' }],
  comment: ['#'],
  header: 0,
  timezone: 'UTC',
  encoding: 'utf-8',
};

describe('CSV parser form transformations', () => {
  it('converts API data to editable form data', () => {
    const formData = apiToForm(apiData);

    expect(formData.pandas_read_csv).toBe(`{
  "na_values": [
    "-",
    "NA"
  ]
}`);
    expect(formData.footlines_to_exclude).toBe(0);
    expect(formData.header).toBe(0);
    expect(formData.comment).not.toBe(apiData.comment);
  });

  it('creates API data with a parsed JSON object and permission group', () => {
    const result = formToApi(apiToForm(apiData), true);

    expect(result).toEqual(apiData);
  });

  it('omits the permission group from update data', () => {
    const result = formToApi(apiToForm(apiData));

    expect(result).not.toHaveProperty('permission_group_id');
    expect(result.pandas_read_csv).toEqual({ na_values: ['-', 'NA'] });
  });

  it('normalizes empty JSON to null', () => {
    const formData: CsvParserFormData = {
      ...apiToForm(apiData),
      pandas_read_csv: '',
    };

    expect(formToApi(formData).pandas_read_csv).toBeNull();
  });

  it('rejects invalid JSON and non-object JSON values', () => {
    const formData = apiToForm(apiData);

    expect(() => formToApi({ ...formData, pandas_read_csv: '{' })).toThrow(
      'Pandas read csv must contain a valid JSON object',
    );
    expect(() => formToApi({ ...formData, pandas_read_csv: '[1, 2]' })).toThrow(
      'Pandas read csv must contain a valid JSON object',
    );
  });
});
