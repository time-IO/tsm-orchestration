import type { PermissionGroup } from 'src/services/permission_group/types';
import type { ParserRead } from 'src/services/types';

export type IngestExternalMqttPublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  description: string | null;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  parser_id: number;
  parser: ParserRead;
  external_mqtt_address: string;
  external_mqtt_port: number;
  external_mqtt_topic: string;
  external_mqtt_username: string | null;
  external_mqtt_password: string | null;
  external_mqtt_ca_cert: string | null;
  external_mqtt_client_cert: string | null;
  external_mqtt_client_key: string | null;
  enabled: boolean;
};

export type IngestExternalMqttCreate = {
  permission_group_id: number | null;
  name: string | null;
  description: string | null;
  parser_id: number | null;
  external_mqtt_address: string | null;
  external_mqtt_port: number | null;
  external_mqtt_topic: string | null;
  external_mqtt_username: string | null;
  external_mqtt_password: string | null;
  external_mqtt_ca_cert: string | null;
  external_mqtt_client_cert: string | null;
  external_mqtt_client_key: string | null;
  enabled: boolean;
};

export type IngestExternalMqttUpdate = {
  permission_group_id?: number | null;
  name?: string | null;
  description?: string | null;
  parser_id?: number | null;
  external_mqtt_address?: string | null;
  external_mqtt_port?: number | null;
  external_mqtt_topic?: string | null;
  external_mqtt_username?: string | null;
  external_mqtt_password?: string | null;
  external_mqtt_ca_cert?: string | null;
  external_mqtt_client_cert?: string | null;
  external_mqtt_client_key?: string | null;
  enabled?: boolean;
};
