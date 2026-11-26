export interface IngestSchedule {
  cron_expression: string | null;
  jitter_seconds: number;
  enabled: boolean;
  sync_interval_minutes: number | null;
  updated_at: string;
  next_runs: string[];
}

export interface ScheduledJob {
  id: number;
  job_type: string;
  params: { days?: number; origin?: string };
  cron_expression: string;
  jitter_seconds: number;
  enabled: boolean;
  note: string | null;
  updated_at: string;
  next_runs: string[];
}

export interface IngestScheduleInfo {
  schedule: IngestSchedule | null;
  jobs: ScheduledJob[];
}
