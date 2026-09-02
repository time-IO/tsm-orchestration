import type { PermissionGroup } from 'src/services/permission_group/types';

export type SoilcanParserPublic = {
  id: number;
  uuid: string;
  created_by_id: number;
  created_at: string;
  name: string;
  description: string | null;
  permission_group_id: number;
  permission_group: PermissionGroup;
  type: string;
  header: boolean;
};

export type SoilcanParserCreate = {
  name: string;
  permission_group_id: number | null;
  description: string | null;
  type: string;
  header: boolean;
};

export type SoilcanParserUpdate = {
  name?: string;
  description?: string | null;
  type?: string;
  header?: boolean;
};
