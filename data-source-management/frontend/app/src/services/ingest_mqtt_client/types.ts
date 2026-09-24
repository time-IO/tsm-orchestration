export type MqttLiveMessage = {
  topic: string;
  payload: string;
  received_at: string;
};

export type MqttLiveHandlers = {
  onOpen?: () => void;
  onConnected?: (topic: string) => void;
  onMessage?: (message: MqttLiveMessage) => void;
  onPublished?: (topic: string) => void;
  onDropped?: (count: number) => void;
  onError?: (detail: string) => void;
  onClose?: () => void;
};
