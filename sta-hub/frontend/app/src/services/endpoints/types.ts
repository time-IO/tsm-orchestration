export type FrostEndpoint = {
  name: string;
  display_name: string;
  group: string;
  project: string | null;
  url: string;
  public_url: string;
  internal_url: string;
  is_internal: boolean;
};

export type FrostEndpointsResponse = {
  endpoints: FrostEndpoint[];
};
