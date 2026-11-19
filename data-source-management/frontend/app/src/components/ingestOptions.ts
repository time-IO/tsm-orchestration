import type { IngestFlowType } from '@/components/ingestDataFlow';

/** One ingest type the user can create, shown as a card on the create-ingest page. */
export interface IngestOption {
  name: string;
  label: string;
  description: string;
  flow: IngestFlowType;
  path?: string;
  /** Pick the concrete API in a searchable dropdown before creating. */
  apiSelect?: boolean;
  /** Longer, user-facing explanation shown in the help dialog. */
  helpText: string;
  /** Situations in which this ingest is the right choice. */
  chooseIf: string[];
}

/** Ingest types grouped by protocol. */
export interface IngestCluster {
  name: string;
  icon: string;
  label: string;
  description: string;
  items: IngestOption[];
}

export interface ExternalApi {
  name: string;
  label: string;
  path: string;
  docsUrl?: string;
}
