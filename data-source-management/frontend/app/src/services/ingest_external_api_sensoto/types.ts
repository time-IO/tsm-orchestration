import type { PermissionGroup } from 'src/services/permission_group/types';

export type IngestExternalApiSensotoPublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  description: string | null;
  network: string;
  device: string;
  sync_enabled: boolean;
  sync_interval_in_minutes: number;
  period_in_minutes: number | null;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
};

export type IngestExternalApiSensotoCreate = {
  permission_group_id: number | null;
  name: string;
  network: string;
  device: string;
  description: string | null;
  sync_enabled: boolean;
  sync_interval_in_minutes: number | null;
  period_in_minutes: number | null;
};

export type IngestExternalApiSensotoUpdate = {
  permission_group_id?: number | null;
  name?: string;
  network?: string;
  device?: string;
  description?: string | null;
  sync_enabled?: boolean;
  sync_interval_in_minutes?: number | null;
  period_in_minutes?: number | null;
};
