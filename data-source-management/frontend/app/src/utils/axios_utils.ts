import { i18n } from '@/boot/i18n';
import type { AxiosError } from 'axios';

/**
 * Resolves an error code and keyword into a localized error message.
 *
 * Looks up the i18next key `axios.errors.<errorCode>.<keyword>`, falling back to
 * `errors.<errorCode>.default` if the keyword is not defined for that code.
 *
 * If the error code itself is unknown, falls back to `errors.unknown`.
 *
 * @param code - The error code, e.g. 401, 404, 500.
 * @param keyword - The keyword identifying the specific message, e.g. "user", "token".
 * @returns {string} The localized, resolved error message.
 */
export function getErrorTextByStatusCode(code?: number | null, keyword?: string | null): string {
  const tPath = 'axios.errors';

  const specificKey = `${tPath}.${code ?? ''}.${keyword?.trim().toLowerCase() ?? 'default'}`;
  const defaultKey = `${tPath}.${code ?? ''}.default`;
  const unknownKey = `${tPath}.unknown`;

  if (i18n.global.te(specificKey)) {
    return String(i18n.global.t(specificKey));
  }
  if (i18n.global.te(defaultKey)) {
    return String(i18n.global.t(defaultKey));
  }
  return String(i18n.global.t(unknownKey));
}

/**
 * Resolves an Axios error into a localized error message.
 *
 * Extracts the HTTP status code from the Axios error's response (or `null`
 * if there is none, e.g. on a network error) and delegates to
 * {@link getErrorTextByStatusCode}.
 *
 * @param error - The Axios error to resolve a message for.
 * @param keyword - The keyword identifying the specific message, e.g. "user", "token".
 * @returns {string} The localized, resolved error message.
 */
export function getErrorTextByAxiosError(error: AxiosError, keyword?: string): string {
  const status = error.response?.status ?? null;
  return getErrorTextByStatusCode(status, keyword);
}

/**
 * Returns generic error message for fetching a resource.
 *
 * @param resourceToFetch - The name of the resource that will appear in the message.
 * @returns {string} The error message.
 */
export function getGenericFetchingError(resourceToFetch: string): string {
  const tPath = 'axios.errors';
  const genericErrorKey = `${tPath}.generic.failedToFetch`;
  return i18n.global.t(genericErrorKey, { resource: resourceToFetch });
}
