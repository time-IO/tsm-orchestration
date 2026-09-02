import type { PermissionGroup } from 'src/services/permission_group/types';

export type IngestExternalApiTheThingsNetworkPublic = {
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
  api_key: string;
  endpoint_uri: string;
};

export type IngestExternalApiTheThingsNetworkCreate = {
  permission_group_id: number | null;
  name: string;
  description: string | null;
  sync_enabled: boolean;
  sync_interval_in_minutes: number | null;
  api_key: string | null;
  endpoint_uri: string | null;
};

export type IngestExternalApiTheThingsNetworkUpdate = {
  permission_group_id?: number | null;
  name?: string | null;
  description?: string | null;
  sync_enabled?: boolean | null;
  sync_interval_in_minutes?: number | null;
  api_key?: string | null;
  endpoint_uri?: string | null;
};
