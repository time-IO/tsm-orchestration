export type FrostEndpoint = {
  name: string;
  displayName: string;
  group: string;
  project: string | null;
  url: string;
  is_own: boolean;
};

export type FrostEndpointsResponse = {
  endpoints: FrostEndpoint[];
};
