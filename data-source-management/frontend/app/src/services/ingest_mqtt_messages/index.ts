import { axiosInstance } from '@/boot/axios';
import type { MqttMessageQuery, MqttMessageResponse } from '@/services/ingest_mqtt_messages/types';

const apiPath = '/ingest';

async function fetchMqttMessages(ingestId: number, query: MqttMessageQuery) {
  return await axiosInstance.get<MqttMessageResponse>(`${apiPath}/${ingestId}/mqtt_messages`, {
    params: query,
  });
}

export default {
  fetchMqttMessages,
};
