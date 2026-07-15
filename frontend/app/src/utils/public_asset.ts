export function publicAsset(path: string): string {
  const normalizedPath = path.startsWith('/') ? path.slice(1) : path;
  return `${import.meta.env.BASE_URL}${normalizedPath}`;
}
