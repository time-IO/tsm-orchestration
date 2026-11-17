export function isPredefinedParser(
  parser: { parser_type?: string | null | undefined } | null | undefined,
): boolean {
  return parser?.parser_type === 'predefined';
}

const PREDEFINED_PARSER_DISPLAY_NAMES: Record<string, string> = {
  campbell_cr6: 'Campbell CR6',
  chirpstack_generic: 'ChirpStack Generic',
  quaesta: 'Quaesta',
  truelog100: 'TrueLog100',
  ydoc_ml417: 'Ydoc ML417',
};

export function parserDisplayName(
  name: string | null | undefined,
  parserType: string | null | undefined,
): string {
  if (!name) return '';
  if (parserType !== 'predefined') return name;
  return PREDEFINED_PARSER_DISPLAY_NAMES[name] ?? name;
}
