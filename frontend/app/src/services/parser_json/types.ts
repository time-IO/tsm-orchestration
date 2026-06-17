import type { PermissionGroup } from 'src/services/permission_group/types';

export type JsonParserTimestampKeyCreate = {
  key: string | null;
  format: string | null;
};
export type JsonParserTimestampKeyUpdate = {
  key: string | null;
  format: string | null;
};
export type JsonParserTimestampKeyPublic = {
  id: number;
  key: string | null;
  format: string | null;
};

export type JsonParserPublic = {
  id: number;
  uuid: string;
  created_by_id: number;
  created_at: string;
  name: string;
  description: string | null;
  comment: string | null;
  timestamp_keys: Array<JsonParserTimestampKeyPublic>;
  permission_group_id: number;
  permission_group: PermissionGroup;
};

export type JsonParserCreate = {
  name: string;
  permission_group_id: number | null;
  description: string | null;
  comment: string | null;
  timestamp_keys: Array<JsonParserTimestampKeyCreate>;
};

export type JsonParserUpdate = {
  name?: string;
  description?: string | null;
  comment?: string | null;
  timestamp_keys?: Array<JsonParserTimestampKeyUpdate> | null;
};
