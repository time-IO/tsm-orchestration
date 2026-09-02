export type UsageStatisticsCounts = {
  projects: number;
  users: number;
  ingest_external_api_bosch: number;
  ingest_external_api_dwd: number;
  ingest_external_api_neutronmonitor: number;
  ingest_external_api_thethingsnetwork: number;
  ingest_external_api_tsystems: number;
  ingest_external_api_uba: number;
  ingest_external_sftp: number;
  ingest_mqtt: number;
  ingest_s3store: number;
  quality_control_setting: number;
  parser_csv: number;
  parser_json: number;
  ingests: number;
};

export type UsageStatisticsResponse = {
  counts: UsageStatisticsCounts;
};
