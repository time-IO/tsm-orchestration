import type { PermissionGroup } from 'src/services/permission_group/types';
import type { ParserRead } from 'src/services/types';

export type IngestSftpPublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  description: string | null;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  parser_id: number;
  filename_pattern: string;
  username: string;
  password: string;
  bucket_name: string;
  fileserver_uri: string;
  parser: ParserRead;
};

export type IngestSftpCreate = {
  permission_group_id: number | null;
  name: string | null;
  description: string | null;
  parser_id: number | null;
  filename_pattern: string | null;
};

export type IngestSftpUpdate = {
  permission_group_id?: number | null;
  name?: string | null;
  description?: string | null;
  parser_id?: number | null;
  filename_pattern?: string | null;
};
