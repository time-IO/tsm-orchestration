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
};

export function isDatastreamType(
  arg: QualityControlFunctionArgumentBase,
): arg is QualityControlFunctionArgumentBase & {
  input: { value: Datastream[] };
} {
  return arg.type === 'datastream';
}

export interface FunctionOption {
  label: string;
  description: string;
}
