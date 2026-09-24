export type TriggerSyncExtApiBase = {
  ingest_ids: number[];
  start_date: string;
  end_date: string;
};

export type TriggerSyncExtApiResponse = {
  triggered_ingests: number[];
};
