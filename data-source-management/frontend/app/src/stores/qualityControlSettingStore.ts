import { acceptHMRUpdate } from 'pinia';
import type {
  QualityControlSettingCreate,
  QualityControlSettingPublic,
  QualityControlSettingUpdate,
} from '@/services/quality_control_setting/types';
import { API } from '@/services';
import { createIngestStore } from '@/stores/factoryIngestStore';

export const useQualityControlSettingStore = createIngestStore<
  QualityControlSettingPublic,
  QualityControlSettingCreate,
  QualityControlSettingUpdate
>('qualityControlSettingStore', API.qualityControlSetting);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useQualityControlSettingStore, import.meta.hot));
}
