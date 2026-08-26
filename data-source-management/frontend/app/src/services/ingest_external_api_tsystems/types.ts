import type { PermissionGroup } from 'src/services/permission_group/types';

export type IngestExternalApiTSystemsPublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  description: string | null;
  sync_enabled: boolean;
  sync_interval_in_minutes: number;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  group: string;
  station_id: string;
  tsystems_username: string;
  tsystems_password: string;
};

export type IngestExternalApiTSystemsCreate = {
  permission_group_id: number | null;
  name: string;
  description: string | null;
  sync_enabled: boolean;
  sync_interval_in_minutes: number | null;
  group: string | null;
  station_id: string | null;
  tsystems_username: string | null;
  tsystems_password: string | null;
};

export type IngestExternalApiTSystemsUpdate = {
  permission_group_id?: number | null;
  name?: string | null;
  description?: string | null;
  sync_enabled?: boolean;
  sync_interval_in_minutes?: number | null;
  api_key?: string | null;
  endpoint_uri?: string | null;
  group?: string | null;
  station_id?: string | null;
  tsystems_username?: string | null;
  tsystems_password?: string | null;
};
