export type TriggerSyncExtSftpBase = {
  ingest_id: number;
  start_date?: string;
  end_date?: string;
};

export type TriggerSyncExtSftpResponse = {
  triggered_ingest: number;
};
