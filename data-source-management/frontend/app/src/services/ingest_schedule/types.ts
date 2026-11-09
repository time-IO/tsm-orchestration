export interface IngestSchedule {
  cron_expression: string;
  jitter_seconds: number;
  enabled: boolean;
  updated_at: string;
  next_runs: string[];
}

export interface CustomJob extends IngestSchedule {
  id: number;
  job_type: string;
  // null for project-wide jobs, which cannot be edited here
  ingest_id: number | null;
  params: { days?: number; origin?: string };
  note: string | null;
}

export interface IngestScheduleInfo {
  schedule: IngestSchedule | null;
  jobs: CustomJob[];
}

export interface CustomJobParamSpec {
  name: string;
  label: string;
  type: string;
  default: number;
  minimum: number;
  maximum: number;
}

export interface CustomJobSpec {
  job_type: string;
  label: string;
  description: string;
  params: CustomJobParamSpec[];
}

export interface CustomJobInput {
  job_type?: string;
  cron_expression: string;
  jitter_seconds?: number | null;
  enabled: boolean;
  params: Record<string, number>;
  note: string | null;
}
