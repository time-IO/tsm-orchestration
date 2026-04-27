import type { Datastream } from 'src/services/sta/types';

// ##### rules - start #####

export const requiredRule = (label: string) => (val: string | number) => 
  (val !== undefined && val !== null && val !== '') || `${label} is required`;

const offsetAliasRegex =
  /^(\d+)?(Y|YS|A|AS|Q|QS|M|MS|W(-MON|-TUE|-WED|-THU|-FRI|-SAT|-SUN)?|SM|SMS|D|B|C|BM|BMS|BQ|BQS|BY|BYS|CBM|CBMS|CQ|CQS|H|T|min|S|L|ms|U|us|N)$/;

export const offsetAliasMatchRule = (val: string) =>
  !val ||
  offsetAliasRegex.test(val) ||
  'value is not a regular offset, please check the documentation';

export const requiredDatastreamsRule = (val: Datastream[] | null) =>
  (Array.isArray(val) && val.length > 0) || 'At least one field datastream is required';

export const integerRule = (val: string) =>
  !val || Number.isInteger(Number(val)) || 'value should be a whole number';

export const numberGreaterThanEqualsRule = (minimum: number) => (val: string) =>
  !val || Number(val) >= minimum || `value should be greater than or equals ${minimum}`;
export const numberLowerThanEqualsRule = (maximum: number) => (val: string) =>
  !val || Number(val) <= maximum || `value should be lower than  or equals ${maximum}`;

// ##### rules - end #####
