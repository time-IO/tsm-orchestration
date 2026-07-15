import type {
  QualityControlSettingPublic,
  QualityControlSettingCreate,
  QualityControlSettingUpdate,
} from 'src/services/quality_control_setting/types';
import { createIngestApiService } from 'src/services/factoryIngestService';

const apiPath = '/quality-control-setting/';

export default createIngestApiService<
  QualityControlSettingPublic,
  QualityControlSettingCreate,
  QualityControlSettingUpdate
>(apiPath);
