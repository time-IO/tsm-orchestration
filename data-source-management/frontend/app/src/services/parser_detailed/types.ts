import type { PermissionGroup } from 'src/services/permission_group/types';

export type ParserDetailedRead = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  description: string | null;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  parser_type: string;
};
