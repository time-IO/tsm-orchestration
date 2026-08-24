import type { PermissionGroup } from 'src/services/permission_group/types';

export type IngestExternalApiRead = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  description: string | null;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  ingest_type: string;
  parser_id: number | null;
  external_api_type: string | null;
  api_type: string;
  sync_enabled: boolean;
  sync_interval_in_minutes: number | null;
};
