export type FrostEndpoint = {
  name: string;
  displayName: string;
  group: string;
  project: string | null;
  url: string;
};

export type FrostEndpointsResponse = {
  endpoints: FrostEndpoint[];
};
