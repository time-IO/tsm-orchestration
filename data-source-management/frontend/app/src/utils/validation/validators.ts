import {
  contextWindowRegex,
  datastreamAliasRegex,
  httpsUrlRegex,
} from 'src/utils/validation/regex';

/**
 * Checks if a value is a valid datastream alias.
 */
export function isDatastreamAlias(val: string): boolean {
  return String(val).match(datastreamAliasRegex) !== null;
}

/**
 * Checks if a value matches the context window regex.
 */
export function isContextWindow(val: string): boolean {
  return String(val).match(contextWindowRegex) !== null;
}

/**
 * Checks if a value matches the context window regex.
 */
export function isHttpsUrl(val: string): boolean {
  return String(val).match(httpsUrlRegex) !== null;
}

/**
 * see https://pandas.pydata.org/docs/reference/api/pandas.Period.strftime.html
 */
export const allowedTimestampTokens: string[] = [
  '%a',
  '%A',
  '%b',
  '%B',
  '%c',
  '%d',
  '%f',
  '%F',
  '%H',
  '%I',
  '%j',
  '%m',
  '%M',
  '%p',
  '%q',
  '%S',
  '%l',
  '%u',
  '%n',
  '%U',
  '%w',
  '%W',
  '%x',
  '%X',
  '%y',
  '%Y',
  '%Z',
];
