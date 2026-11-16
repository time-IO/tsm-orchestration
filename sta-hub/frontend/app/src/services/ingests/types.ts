export type Ingest = {
  id: number;
  uuid: string;
  name: string;
  permission_group_id: number;
  permission_group_name: string | null;
};

export type IngestsResponse = {
  items: Ingest[];
};
