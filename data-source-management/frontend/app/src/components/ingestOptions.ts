import type { IngestFlowType } from '@/components/ingestDataFlow';

export interface IngestOption {
  name: string;
  label: string;
  description: string;
  flow: IngestFlowType;
  path?: string;
  /** a concrete variant (e.g. the external API) in a searchable dropdown */
  variantSelect?: boolean;
  /** longer, user-facing explanation shown in the help dialog */
  helpText: string;
  /** rendered as bullet points in the help dialog */
  chooseIf: string[];
}

export interface IngestCluster {
  name: string;
  icon: string;
  label: string;
  description: string;
  items: IngestOption[];
}

/** A concrete variant of an ingest type, e.g. one external API. */
export interface IngestVariant {
  name: string;
  label: string;
  path: string;
  docsUrl?: string;
}
