import { describe, expect, it } from 'vitest';
import { parserDisplayName } from '@/utils/parser_utils';

describe('parserDisplayName', () => {
  it.each([
    ['campbell_cr6', 'Campbell CR6'],
    ['chirpstack_generic', 'ChirpStack Generic'],
    ['quaesta', 'Quaesta'],
    ['truelog100', 'TrueLog100'],
    ['ydoc_ml417', 'Ydoc ML417'],
  ])('labels the predefined parser %s as %s', (name, label) => {
    expect(parserDisplayName(name, 'predefined')).toBe(label);
  });

  it('keeps unknown predefined names unchanged', () => {
    expect(parserDisplayName('new_device', 'predefined')).toBe('new_device');
  });

  it.each(['csv', 'json', 'soilcan', undefined])(
    'never relabels a user-defined parser (type %s)',
    (parserType) => {
      expect(parserDisplayName('truelog100', parserType)).toBe('truelog100');
    },
  );

  it('returns an empty string for a missing name', () => {
    expect(parserDisplayName(null, 'predefined')).toBe('');
  });
});
