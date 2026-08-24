import type { PermissionGroup } from 'src/services/permission_group/types';
import type { NeutronMonitorStation } from 'src/services/neutron_monitor_stations/types';

export type IngestExternalApiNeutronMonitorPublic = {
  id: number;
  uuid: string;
  name: string;
  description: string | null;
  permission_group_id: number;
  permission_group: PermissionGroup;
  created_by_id: number;
  created_at: string;
  sync_enabled: boolean;
  sync_interval_in_minutes: number;
  station_id: number;
  time_resolution_in_minutes: number;
  station: NeutronMonitorStation;
};
export type IngestExternalApiNeutronMonitorCreate = {
  name: string;
  description: string | null;
  permission_group_id: number | null;
  sync_enabled: boolean;
  sync_interval_in_minutes: number | null;
  station_id: number | null;
  time_resolution_in_minutes: number | null;
};
export type IngestExternalApiNeutronMonitorUpdate = {
  name?: string;
  description?: string | null;
  permission_group_id?: number | null;
  sync_enabled?: boolean;
  sync_interval_in_minutes?: number | null;
  station_id?: number | null;
  time_resolution_in_minutes?: number | null;
};
