export type S3ObjectEntry = {
  name: string;
  key: string;
  size: number;
  last_modified: string | null;
  is_dir: boolean;
};
