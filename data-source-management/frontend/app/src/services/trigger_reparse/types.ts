export type TriggerReparseBase = {
  ingest_id: number;
  start_date?: string;
  end_date?: string;
  filename_pattern?: string;
  parser_id?: number;
  include_parsed: boolean;
  parsed_files_parser: 'current' | 'original';
};

export type TriggerReparseResponse = {
  triggered_ingest: number;
};
