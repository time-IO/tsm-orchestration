import type { QualityControlFunctionArgumentBase } from 'src/services/quality_control_setting/types';
import type { Datastream } from 'src/services/sta/types';

export const POSSIBLE_QC_FUNCTION_TYPES = {
  INT: 'int',
  OFFSET: 'offset',
  DATASTREAM: 'datastream',
  FLOAT: 'float',
  BOOL: 'bool',
  ENUM: 'enum',
  STR: 'str',
  FUNCTION: 'function',
};

export function isDatastreamType(
  arg: QualityControlFunctionArgumentBase,
): arg is QualityControlFunctionArgumentBase & {
  input: { value: Datastream[] };
} {
  return arg.type === 'datastream';
}

export const FUNCTIONS_WITH_REQUIRED_TARGET = ['processGeneric', 'flagGeneric'];

export interface FunctionOption {
  label: string;
  description: string;
}

export function showContextDocumentation(): void {
  window.open(
    'https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#period-aliases',
    '_blank',
  );
}
