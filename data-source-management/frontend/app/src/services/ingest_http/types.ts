import type { PermissionGroup } from 'src/services/permission_group/types';
import type { ParserRead } from 'src/services/types';

export type IngestHttpPublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  description: string | null;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  parser_id: number;
  parser: ParserRead;
  path_for_posts: string;
  file_type: string;
  api_key: string | null;
  enabled: boolean;
};

export type IngestHttpCreate = {
  permission_group_id: number | null;
  name: string | null;
  description: string | null;
  parser_id: number | null;
  path_for_posts: string | null;
  file_type: string | null;
  api_key: string | null;
  enabled: boolean;
};

export type IngestHttpUpdate = {
  permission_group_id?: number | null;
  name?: string | null;
  description?: string | null;
  parser_id?: number | null;
  path_for_posts?: string | null;
  file_type?: string | null;
  api_key?: string | null;
  enabled?: boolean;
};
