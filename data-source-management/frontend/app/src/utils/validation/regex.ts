export const datastreamAliasRegex = /^T\d+S[\dA-Za-z]+$/;

export const contextWindowRegex =
  /^\d+(Y|YS|A|AS|Q|QS|M|MS|W(-MON|-TUE|-WED|-THU|-FRI|-SAT|-SUN)?|SM|SMS|D|B|C|BM|BMS|BQ|BQS|BY|BYS|CBM|CBMS|CQ|CQS|H|T|minRule|S|L|ms|U|us|N)?$/;

export const httpsUrlRegex = /^https:\/\/(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:[/?#][^\s]*)?$/;
