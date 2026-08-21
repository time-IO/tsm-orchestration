import type { PermissionGroup } from 'src/services/permission_group/types';

export type IngestExternalApiUbaPublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  station_id: string;
  description: string | null;
  sync_enabled: boolean;
  sync_interval_in_minutes: number;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
};

export type IngestExternalApiUbaCreate = {
  permission_group_id: number | null;
  name: string;
  station_id: string | null;
  description: string | null;
  sync_enabled: boolean;
  sync_interval_in_minutes: number | null;
};

export type IngestExternalApiUbaUpdate = {
  permission_group_id?: number | null;
  name?: string;
  station_id?: string | null;
  description?: string | null;
  sync_enabled?: boolean;
  sync_interval_in_minutes?: number | null;
};
