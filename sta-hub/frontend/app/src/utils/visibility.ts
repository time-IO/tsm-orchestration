import type { FrostEndpoint } from '@/services/endpoints/types';

export type VisibilityName = 'public' | 'internal';

export type Visibility = {
  label: string;
  icon: string;
  color: string;
};

export const VISIBILITIES: Record<VisibilityName, Visibility> = {
  public: {
    label: 'Public',
    icon: 'visibility',
    color: 'green',
  },
  internal: {
    label: 'Internal',
    icon: 'lock_open',
    color: 'orange',
  },
};

export function endpointVisibility(endpoint: FrostEndpoint): VisibilityName {
  return endpoint.is_internal ? 'internal' : 'public';
}
