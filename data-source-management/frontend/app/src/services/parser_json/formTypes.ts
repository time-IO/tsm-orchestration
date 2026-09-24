import type { JsonParserCreate, JsonParserUpdate } from './types';

export type JsonParserFormData = JsonParserUpdate & {
  permission_group_id?: number | null;
  timestamp_keys: JsonParserCreate['timestamp_keys'];
  excluded_keys: string[];
};
