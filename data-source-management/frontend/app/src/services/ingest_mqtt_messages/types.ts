export interface MqttMessage {
  id: number;
  timestamp: string;
  message: string;
}

export interface MqttMessageResponse {
  mqtt_messages: MqttMessage[];
  total: number;
  page_number: number;
  page_size: number;
}

export interface MqttMessageQuery {
  datetime_from?: string | undefined;
  datetime_to?: string | undefined;
  page_number: number;
  page_size: number;
  order: 'asc' | 'desc';
}
