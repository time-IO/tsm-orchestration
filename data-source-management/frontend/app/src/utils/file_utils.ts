/**
 * Checks whether two files are equal by comparing their name, size, type and last modified.
 */
export function fileMetadataIsEqual(a: File, b: File): boolean {
  return (
    a.name === b.name && a.size === b.size && a.lastModified === b.lastModified && a.type === b.type
  );
}

/**
 * File extensions and MIME types preselected in the file picker when validating a CSV parser.
 */
export const CSV_PARSER_FILE_TYPES = [
  '.csv',
  '.tsv',
  '.txt',
  '.dat',
  '.asc',
  '.tab',
  'text/csv',
  'text/plain',
  'text/tab-separated-values',
];

/**
 * File extensions and MIME types preselected in the file picker when validating a JSON parser.
 */
export const JSON_PARSER_FILE_TYPES = [
  '.json',
  '.geojson',
  '.txt',
  'application/json',
  'application/geo+json',
  'text/plain',
];
