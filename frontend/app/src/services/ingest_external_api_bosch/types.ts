import type { PermissionGroup } from 'src/services/permission_group/types';

export type IngestExternalApiBoschPublic = {
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
  endpoint: string;
  sensor_id: string;
  bosch_username: string;
  bosch_password: string;
  period_in_minutes: number;
};

export type IngestExternalApiBoschCreate = {
  permission_group_id: number | null;
  name: string;
  description: string | null;
  sync_enabled: boolean;
  sync_interval_in_minutes: number | null;
  endpoint: string | null;
  sensor_id: string | null;
  bosch_username: string | null;
  bosch_password: string | null;
  period_in_minutes: number | null;
};

export type IngestExternalApiBoschUpdate = {
  permission_group_id?: number | null;
  name?: string;
  description?: string | null;
  sync_enabled?: boolean;
  sync_interval_in_minutes?: number | null;
  endpoint?: string | null;
  sensor_id?: string | null;
  bosch_username?: string | null;
  bosch_password?: string | null;
  period_in_minutes?: number | null;
};
