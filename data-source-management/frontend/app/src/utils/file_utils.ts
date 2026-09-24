/**
 * Checks whether two files are equal by comparing their name, size, type and last modified.
 */
export function fileMetadataIsEqual(a: File, b: File): boolean {
  return (
    a.name === b.name && a.size === b.size && a.lastModified === b.lastModified && a.type === b.type
  );
}
