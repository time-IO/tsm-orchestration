export type TriggerQCSBase = {
  quality_control_setting_ids: number[];
  start_date: string;
  end_date: string;
};

export type TriggerQCSResponse = {
  triggered_quality_control_settings: number[];
};
