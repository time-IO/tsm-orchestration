import type {PermissionGroup} from "src/services/permission_group/types";
import type { MqttParser } from 'src/services/mqtt_parser/type';

export type IngestMqttPublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  description: string | null;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  topic: string;
  uri: string;
  username: string;
  password: string;
  mqtt_parser: MqttParser;
};

export type IngestMqttCreate = {
  permission_group_id: number | null;
  name: string | null;
  description: string | null;
  topic: string | null;
  uri: string | null;
  mqtt_parser_id: number | null
};

export type IngestMqttUpdate = {
  permission_group_id?: number | null;
  name?: string | null;
  description?: string | null;
  topic?: string | null;
  uri?: string | null;
  mqtt_parser_id?: number | null;
};
