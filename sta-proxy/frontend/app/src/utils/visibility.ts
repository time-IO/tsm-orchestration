import type { FrostEndpoint } from '@/services/endpoints/types';

export type VisibilityName = 'public' | 'internal';

export type Visibility = {
  label: string;
  icon: string;
  color: string;
  description: string;
};

export const VISIBILITIES: Record<VisibilityName, Visibility> = {
  public: {
    label: 'Public',
    icon: 'visibility',
    color: 'green',
    description: 'Listed for everyone, no login required to find the endpoint.',
  },
  internal: {
    label: 'Internal',
    icon: 'lock_open',
    color: 'orange',
    description: 'Belongs to one of your projects (permission groups). Only shown after login.',
  },
};

export function endpointVisibility(endpoint: FrostEndpoint): VisibilityName {
  return endpoint.is_internal ? 'internal' : 'public';
}
