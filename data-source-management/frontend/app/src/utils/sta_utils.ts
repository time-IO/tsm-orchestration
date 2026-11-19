import type { Datastream } from '@/services/sta/types';

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

/**
 * Groups datastreams by the name of their thing, keeping the order of first appearance.
 * @param datastreams - The datastreams to group
 * @returns One group per thing name; datastreams without a thing are grouped under '-'
 */
export function groupDatastreamsByThing(
  datastreams: Datastream[],
): { thingName: string; datastreams: Datastream[] }[] {
  const groups = new Map<string, Datastream[]>();
  datastreams.forEach((ds) => {
    const thingName = ds.Thing?.name || '-';
    groups.set(thingName, [...(groups.get(thingName) ?? []), ds]);
  });
  return Array.from(groups, ([thingName, datastreams]) => ({ thingName, datastreams }));
}
