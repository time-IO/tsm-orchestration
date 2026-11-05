export interface IngestSchedule {
  cron_expression: string;
  jitter_seconds: number;
  enabled: boolean;
  updated_at: string;
  next_runs: string[];
}

export interface ScheduledJob extends IngestSchedule {
  id: number;
  job_type: string;
  scope: 'ingest' | 'project';
  params: { days?: number; origin?: string };
  note: string | null;
}

export interface IngestScheduleInfo {
  schedule: IngestSchedule | null;
  jobs: ScheduledJob[];
}
