import type { PermissionGroup } from 'src/services/permission_group/types';
import type { Datastream } from 'src/services/sta/types';

export type QualityControlFunctionArgumentBase = {
  name: string;
  type: string;
  input: {
    value: number | string | Datastream[] | boolean | null;
  };
};

export type QualityControlFunctionArgumentPublic = QualityControlFunctionArgumentBase & {
  id: number;
};

export type QualityControlFunctionArgumentCreate = QualityControlFunctionArgumentBase;
export type QualityControlFunctionArgumentUpdate = QualityControlFunctionArgumentBase;

export type QualityControlFunctionPublic = {
  id: number;
  name: string;
  label?: string | null | undefined;
  quality_control_function_arguments: QualityControlFunctionArgumentPublic[];
};

export type QualityControlFunctionCreate = {
  name: string;
  label?: string | null | undefined;
  quality_control_function_arguments: QualityControlFunctionArgumentCreate[];
};

export type QualityControlFunctionUpdate = {
  name: string;
  label?: string | null | undefined;
  quality_control_function_arguments: QualityControlFunctionArgumentUpdate[];
};

export type QualityControlSettingPublic = {
  id: number;
  uuid: string;
  permission_group_id: number;
  name: string;
  context_window: string;
  description: string | null;
  is_active: boolean;
  created_by_id: number;
  created_at: string;
  permission_group: PermissionGroup;
  quality_control_functions: QualityControlFunctionPublic[];
};

export type QualityControlSettingCreate = {
  permission_group_id: number | null;
  name: string | null;
  context_window: string | null;
  description: string | null;
  is_active: boolean | null;
  quality_control_functions: QualityControlFunctionCreate[];
};

export type QualityControlSettingUpdate = {
  permission_group_id?: number | null;
  name?: string | null;
  context_window?: string | null;
  description?: string | null;
  is_active?: boolean | null;
  quality_control_functions?: QualityControlFunctionUpdate[];
};
