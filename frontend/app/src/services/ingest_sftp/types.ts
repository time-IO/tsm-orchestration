import type { PermissionGroup } from 'src/services/permission_group/types';
import type { CsvParserPublic } from 'src/services/parser_csv/types';

export type IngestSftpPublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  description: string | null;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  parser_csv_id: number;
  filename_pattern: string;
  username: string;
  password: string;
  bucket_name: string;
  fileserver_uri: string;
  csv_parser: CsvParserPublic;
};

export type IngestSftpCreate = {
  permission_group_id: number | null;
  name: string | null;
  description: string | null;
  parser_csv_id: number | null;
  filename_pattern: string | null;
};

export type IngestSftpUpdate = {
  name?: string | null;
  description?: string | null;
  parser_csv_id?: number | null;
  filename_pattern?: string | null;
};
