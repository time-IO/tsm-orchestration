export interface JournalEntry {
  id: number;
  timestamp: string;
  level: string;
  message: string | null;
  origin: string | null;
  extra: unknown;
}

export interface JournalResponse {
  journal_entries: JournalEntry[];
}

export interface JournalQuery {
  datetime_from?: string;
  datetime_to?: string;
  level?: string;
  limit?: number;
}
