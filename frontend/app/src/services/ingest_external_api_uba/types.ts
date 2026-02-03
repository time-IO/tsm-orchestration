import type {Project} from "src/services/project/types";

export type IngestExternalApiUbaPublic = {
  id: number
  uuid: string;
  project_id: number;
  name: string;
  station_id: number;
  description: string;
  sync_enabled: boolean;
  sync_interval_in_minutes: number;
  created_by_id: number;
  created_at: string;
  project: Project
}

export type IngestExternalApiUbaCreate = {
  project_id: number;
  name: string;
  station_id: number;
  description: string;
  sync_enabled: boolean;
}

export type IngestExternalApiUbaUpdate = {
  project_id?: number;
  name?: string;
  station_id?: number;
  description?: string;
  sync_enabled?: boolean;
}
