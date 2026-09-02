import type { PermissionGroup } from 'src/services/permission_group/types';
import type { ParserRead } from 'src/services/types';

export type IngestExternalSftpPublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  description: string | null;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  parser_id: number;
  uri: string;
  path: string;
  username: string | null;
  password: string | null;
  bucket_username: string;
  bucket_password: string;
  ssh_public_key: string;
  sync_interval_in_minutes: number;
  sync_enabled: boolean;
  parser: ParserRead;
  filename_pattern: string;
};

export type IngestExternalSftpCreate = {
  permission_group_id: number | null;
  name: string | null;
  description: string | null;
  parser_id: number | null;
  uri: string | null;
  path: string | null;
  username: string | null;
  password: string | null;
  sync_interval_in_minutes: number | null;
  sync_enabled: boolean;
  filename_pattern: string | null;
};

export type IngestExternalSftpUpdate = {
  permission_group_id?: number | null;
  name?: string | null;
  description?: string | null;
  parser_id?: number | null;
  uri?: string | null;
  path?: string | null;
  username?: string | null;
  password?: string | null;
  sync_interval_in_minutes?: number | null;
  sync_enabled?: boolean | null;
  filename_pattern?: string | null;
};
