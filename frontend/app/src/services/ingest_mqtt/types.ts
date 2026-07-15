import type { PermissionGroup } from 'src/services/permission_group/types';
import type { ParserRead } from 'src/services/types';

export type IngestMqttPublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  description: string | null;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  username: string;
  password: string;
  topic: string;
  uri: string;
  parser_id: number;
  parser: ParserRead;
};

export type IngestMqttCreate = {
  permission_group_id: number | null;
  name: string | null;
  description: string | null;
  parser_id: number | null;
  username: string | null;
};

export type IngestMqttUpdate = {
  permission_group_id?: number | null;
  name?: string | null;
  description?: string | null;
  parser_id?: number | null;
};
