import type { PermissionGroup } from '@/services/permission_group/types';

export type IngestExternalApiMyAtmospherePublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  customer_id: number;
  serial_number: string;
  period_in_minutes: number | null;
  description: string | null;
  sync_enabled: boolean;
  sync_interval_in_minutes: number | null;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  api_key: string;
};

export type IngestExternalApiMyAtmosphereCreate = {
  name: string;
  description: string | null;
  permission_group_id: number | null;
  customer_id: number | null;
  serial_number: string;
  period_in_minutes: number | null;
  sync_enabled: boolean;
  sync_interval_in_minutes: number | null;
  api_key: string;
};

export type IngestExternalApiMyAtmosphereUpdate = {
  name?: string;
  description?: string | null;
  permission_group_id?: number | null;
  customer_id?: number | null;
  serial_number?: string;
  period_in_minutes?: number | null;
  sync_enabled?: boolean;
  sync_interval_in_minutes?: number | null;
  api_key?: string | null;
};
