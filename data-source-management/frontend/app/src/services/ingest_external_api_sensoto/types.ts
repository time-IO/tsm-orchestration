import type { PermissionGroup } from '@/services/permission_group/types';

export type IngestExternalApiSensotoPublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  description: string | null;
  network: string;
  device: string;
  organization: string;
  sync_enabled: boolean;
  sync_interval_in_minutes: number;
  period_in_minutes: number | null;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  token: string | null;
};

export type IngestExternalApiSensotoCreate = {
  permission_group_id: number | null;
  name: string;
  network: string | null;
  device: string | null;
  description: string | null;
  organization: string | null;
  sync_enabled: boolean;
  sync_interval_in_minutes: number | null;
  period_in_minutes: number | null;
  token: string | null;
};

export type IngestExternalApiSensotoUpdate = {
  permission_group_id?: number | null;
  name?: string;
  network?: string | null;
  device?: string | null;
  organization?: string | null;
  description?: string | null;
  sync_enabled?: boolean;
  sync_interval_in_minutes?: number | null;
  period_in_minutes?: number | null;
  token?: string | null;
};
