import type {
  QualityControlSettingPublic,
  QualityControlSettingCreate,
  QualityControlSettingUpdate,
} from '@/services/quality_control_setting/types';
import { createIngestApiService } from '@/services/factoryIngestService';

const apiPath = '/quality-control-setting/';

export default createIngestApiService<
  QualityControlSettingPublic,
  QualityControlSettingCreate,
  QualityControlSettingUpdate
>(apiPath);
