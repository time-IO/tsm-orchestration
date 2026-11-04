import type { PermissionGroup } from '@/services/permission_group/types';

export type IngestExternalApiZentraPublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  device_sn: string;
  period_in_minutes: number | null;
  units: 'metric' | 'imperial' | null;
  description: string | null;
  sync_enabled: boolean;
  sync_interval_in_minutes: number | null;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  api_key: string;
};

export type IngestExternalApiZentraCreate = {
  name: string;
  description: string | null;
  permission_group_id: number | null;
  device_sn: string;
  period_in_minutes: number | null;
  units: 'metric' | 'imperial' | null;
  sync_enabled: boolean;
  sync_interval_in_minutes: number | null;
  api_key: string;
};

export type IngestExternalApiZentraUpdate = {
  name?: string;
  description?: string | null;
  permission_group_id?: number | null;
  device_sn?: string;
  period_in_minutes?: number | null;
  units?: 'metric' | 'imperial' | null;
  sync_enabled?: boolean;
  sync_interval_in_minutes?: number | null;
  api_key?: string | null;
};
