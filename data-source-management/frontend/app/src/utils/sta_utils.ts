/**
 * Extracts the actual stream name from an STA datastream name.
 * The name consists of several parts separated by ':', the third part is the stream name,
 * e.g. "MyThing:MySensor:temperature:1" -> "temperature".
 * @param name - The full STA datastream name
 * @returns The stream name, or the full name if it has no non-empty third part
 */
export function extractStreamName(name: string | null | undefined): string {
  if (!name) return '';
  const streamName = name.split(':')[2]?.trim();
  return streamName || name;
}
