import { i18n } from 'src/boot/i18n';
import {
  allowedTimestampTokens,
  isContextWindow,
  isDatastreamAlias,
  isHttpsUrl,
} from 'src/utils/validation/validators';
import { date } from 'quasar';
import { formatExact } from 'src/utils/time_utils';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type ValidationRule = (val: any) => boolean | string;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type ValidationRuleFactory<Args extends any[] = any[]> = (...args: Args) => ValidationRule;

/* ================================================== */
/* ValidationRules (fixed rules without parameters)   */
/* ================================================== */

/**
 * Field is required.
 */
const requiredRule: ValidationRule = (val): true | string => {
  if (val || val === 0) return true;
  return i18n.global.t('validation.validatorIsRequired');
};

/**
 * Context window value must be valid if provided.
 */
const contextWindowRule: ValidationRule = (val): true | string => {
  if (!val || isContextWindow(val)) return true;
  return i18n.global.t('validation.validatorIsInvalid');
};

/**
 * Value must be a valid datastream alias.
 */
const datastreamAliasRule: ValidationRule = (val): true | string => {
  if (!val || isDatastreamAlias(val)) return true;
  return i18n.global.t('validation.validatorIsInvalid');
};

/**
 * Validates that a value is an integer number.
 */
const integerRule: ValidationRule = (val): true | string => {
  if (val === null || val === undefined || val === '') return true;

  const num = Number(val);
  if (!Number.isFinite(num) || !Number.isInteger(num)) {
    return i18n.global.t('validation.validatorMustBeInteger');
  }

  return true;
};

/**
 * Validates that a value is a floating-point number.
 */
const floatRule: ValidationRule = (val): true | string => {
  if (val === null || val === undefined || val === '') return true;

  const num = Number(val);
  if (!Number.isFinite(num)) {
    return i18n.global.t('validation.validatorMustBeFloat');
  }

  return true;
};

/**
 * Validates that a value is a valid timestamp format.
 */
const timestampFormatRule: ValidationRule = (val): true | string => {
  const tokens = String(val).match(/%[a-zA-Z]/g) || [];
  const seen: string[] = [];
  for (const token of tokens) {
    if (!allowedTimestampTokens.includes(token))
      return i18n.global.t('validation.timestampTokenNotValid', { token });
    if (seen.includes(token)) return i18n.global.t('validation.timestampTokenDuplicate', { token });
    seen.push(token);
  }
  return true;
};

/**
 * Validates that a value is an array.
 */
const listRule: ValidationRule = (val): true | string => {
  if (val === null || val === undefined || val === '') return true;

  if (!Array.isArray(val)) {
    return i18n.global.t('validation.validatorMustBeList');
  }

  return true;
};

/**
 * Checks whether the provided value is a valid Date object.
 */
const dateRule: ValidationRule = (val): true | string => {
  if (!val) return true;
  if (!(val instanceof Date) || isNaN(val.getTime())) {
    return i18n.global.t('validation.validatorIsInvalid');
  }
  return true;
};

/**
 * Checks whether the provided value is an HTTPS url.
 */
const httpsUrlRule: ValidationRule = (val): true | string => {
  if (!val || isHttpsUrl(val)) return true;
  return i18n.global.t('validation.validatorIsInvalidHttpsUrl');
};

/* ========================================================== */
/* ValidationRuleFactories (rules that take parameters)       */
/* ========================================================== */

/**
 * Minimum value, length, or date.
 * @param min Minimum threshold (number or string).
 * @param format Optional date format. If given, values are treated as dates.
 */
const minRule: ValidationRuleFactory<[number | string, string?]> =
  (min: number | string, format?: string) =>
  (val): true | string => {
    if (val == null || val === '' || min == null || min === '') return true;

    if (!format && typeof val === 'number') {
      return val >= (min as number)
        ? true
        : i18n.global.t('validation.validatorMustNotBeLowerThan', { threshold: min });
    }

    if (format) {
      const parsedVal = date.extractDate(String(val), format);
      const parsedMin = date.extractDate(String(min), format);

      if (!parsedVal || !parsedMin || isNaN(parsedVal.getTime()) || isNaN(parsedMin.getTime())) {
        return i18n.global.t('validation.validatorIsInvalid');
      }

      return parsedVal.getTime() >= parsedMin.getTime()
        ? true
        : i18n.global.t('validation.validatorMustNotBeBefore', {
            threshold: date.formatDate(parsedMin, format),
          });
    }

    if (typeof val === 'string' || Array.isArray(val)) {
      return val.length >= (min as number)
        ? true
        : i18n.global.t('validation.validatorListMustNotBeShorterThan', { threshold: min });
    }

    return i18n.global.t('validation.validatorIsInvalid');
  };

/**
 * Maximum value, length, or date.
 * @param max Maximum threshold (number or string).
 * @param format Optional date format. If given, values are treated as dates.
 */
const maxRule: ValidationRuleFactory<[number | string, string?]> =
  (max: number | string, format?: string) =>
  (val): true | string => {
    if (val == null || val === '' || max == null || max === '') return true;

    if (!format && typeof val === 'number') {
      return val <= (max as number)
        ? true
        : i18n.global.t('validation.validatorMustNotBeGreaterThan', { threshold: max });
    }

    if (format) {
      const parsedVal = date.extractDate(String(val), format);
      const parsedMax = date.extractDate(String(max), format);

      if (!parsedVal || !parsedMax || isNaN(parsedVal.getTime()) || isNaN(parsedMax.getTime())) {
        return i18n.global.t('validation.validatorIsInvalid');
      }

      return parsedVal.getTime() <= parsedMax.getTime()
        ? true
        : i18n.global.t('validation.validatorMustNotBeAfter', {
            threshold: date.formatDate(parsedMax, format),
          });
    }

    if (typeof val === 'string' || Array.isArray(val)) {
      return val.length <= (max as number)
        ? true
        : i18n.global.t('validation.validatorListMustNotBeLongerThan', { threshold: max });
    }

    return i18n.global.t('validation.validatorIsInvalid');
  };

/**
 * Checks if a number, string length, or date is within a range.
 * @param min Minimum threshold (number or string).
 * @param max Maximum threshold (number or string).
 */
const rangeRule: ValidationRuleFactory<[number | string, number | string]> =
  (min: number | string, max: number | string) =>
  (val): true | string => {
    const isValid = ruleFactories.MAX(max)(val) === true && ruleFactories.MIN(min)(val) === true;
    return isValid || i18n.global.t('validation.validatorIsInvalid');
  };

/**
 * Ensures that the time interval is not shorter than the specified interval.
 * @param minInterval Minimum threshold in milliseconds.
 */
const minIntervalRule: ValidationRuleFactory<[number]> = (minInterval: number | null) => {
  return (val): true | string => {
    if (!val || !minInterval) return true;
    return val >= minInterval
      ? true
      : i18n.global.t('validation.validatorIntervalMustNotBeShorterThan', {
          threshold: formatExact(minInterval),
        });
  };
};

/**
 * Ensures that the time interval is not shorter than the specified interval.
 * @param maxInterval Maximum threshold in milliseconds.
 */
const maxIntervalRule: ValidationRuleFactory<[number]> = (maxInterval: number | null) => {
  return (val): true | string => {
    if (!val || !maxInterval) return true;
    return val <= maxInterval
      ? true
      : i18n.global.t('validation.validatorIntervalMustNotBeLongerThan', {
          threshold: formatExact(maxInterval),
        });
  };
};

/**
 * Ensures that the date is not earlier than the specified minimum date.
 * @param minDate Minimum threshold.
 */
const minDateRule: ValidationRuleFactory<[Date]> = (minDate: Date | null) => {
  return (val): true | string => {
    if (!val || !minDate) return true;
    if (!(val instanceof Date)) {
      return true;
    }
    return (
      val.getTime() >= minDate.getTime() ||
      i18n.global.t('validation.validatorMustNotBeBefore', { threshold: minDate.toLocaleString() })
    );
  };
};

/**
 * Ensures that the date is not later than the specified maximum date.
 * @param maxDate Maximum threshold.
 */
const maxDateRule: ValidationRuleFactory<[Date]> = (maxDate: Date | null) => {
  return (val): true | string => {
    if (!val || !maxDate) return true;
    if (!(val instanceof Date)) {
      return true;
    }
    return (
      val.getTime() <= maxDate.getTime() ||
      i18n.global.t('validation.validatorMustNotBeAfter', { threshold: maxDate.toLocaleString() })
    );
  };
};

/**
 * Validates that a date string matches the given format.
 * @param format Date format pattern (e.g. 'DD.MM.YYYY' or 'DD.MM.YYYY HH:mm')
 */
const dateTimeFormatRule: ValidationRuleFactory<[string]> = (format: string) => {
  return (val): true | string => {
    if (!val) return true;

    const parsed = date.extractDate(val, format);
    if (!parsed || isNaN(parsed.getTime())) {
      return i18n.global.t('validation.validatorIsInvalid');
    }
    return true;
  };
};

/**
 * Ensures the value is one of a given list.
 * @param options Allowed values.
 */
const inListRule: ValidationRuleFactory<[unknown[]]> =
  (options) =>
  (val): true | string => {
    if (val === null || val === undefined || val === '') return true;
    return (
      options.includes(val) ||
      i18n.global.t('validation.validatorMustBeOneOf', { options: options.join(', ') })
    );
  };

/**
 * Ensures the value is NOT one of a given list.
 * @param options Disallowed values.
 */
const notInListRule: ValidationRuleFactory<[unknown[]]> =
  (options) =>
  (val): true | string => {
    if (val === null || val === undefined || val === '') return true;
    return (
      !options.includes(val) ||
      i18n.global.t('validation.validatorMustNotBeOneOf', { options: options.join(', ') })
    );
  };

/**
 * Validates a value against a regular expression.
 * @param pattern Regular expression to test against.
 */
const regexRule: ValidationRuleFactory<[RegExp, string?]> =
  (pattern) =>
  (val): true | string => {
    if (val === null || val === undefined || val === '') return true;

    const stringValue = String(val).trim();
    if (pattern.test(stringValue)) return true;

    return i18n.global.t('validation.validatorIsInvalid');
  };

/**
 * Composite rule factory: succeeds if at least one rule passes.
 * Accepts ValidationRules or RuleFactories (invoked without args).
 * @param rules Array of rules or factories.
 */
const anyRule: ValidationRuleFactory<[(ValidationRule | ValidationRuleFactory)[]]> =
  (rules: (ValidationRule | ValidationRuleFactory)[]) =>
  (val): true | string => {
    const results = rules.map((rule) => {
      const fn =
        (rule as ValidationRuleFactory).length > 0
          ? (rule as ValidationRuleFactory)()
          : (rule as ValidationRule);
      return fn(val);
    });

    if (results.some((r) => r === true)) return true;

    return i18n.global.t('validation.validatorIsInvalid');
  };

export const rules = {
  REQUIRED: requiredRule,
  INTEGER: integerRule,
  FLOAT: floatRule,
  LIST: listRule,
  DATE: dateRule,
  DATASTREAM_ALIAS: datastreamAliasRule,
  CONTEXT_WINDOW: contextWindowRule,
  HTTPS_URL: httpsUrlRule,
  TIMESTAMP_FORMAT: timestampFormatRule,
};

export const ruleFactories = {
  MIN: minRule,
  MAX: maxRule,
  RANGE: rangeRule,
  IN_LIST: inListRule,
  NOT_IN_LIST: notInListRule,
  DATE_TIME: dateTimeFormatRule,
  REGEX: regexRule,
  ANY_RULE: anyRule,
  MIN_DATE: minDateRule,
  MAX_DATE: maxDateRule,
  MIN_INTERVAL: minIntervalRule,
  MAX_INTERVAL: maxIntervalRule,
};
