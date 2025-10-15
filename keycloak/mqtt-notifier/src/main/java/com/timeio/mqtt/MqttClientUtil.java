package com.timeio.mqtt;

import org.eclipse.paho.client.mqttv3.*;

public class MqttClientUtil {
    private final MqttClient client;

    public MqttClientUtil(String brokerUrl, String clientId) throws MqttException {
        this.client = new MqttClient(brokerUrl, clientId, null);
        MqttConnectOptions opts = new MqttConnectOptions();
        opts.setAutomaticReconnect(true);
        opts.setCleanSession(true);
        client.connect(opts);
    }

    public void publish(String topic, String payload) throws MqttException {
        MqttMessage msg = new MqttMessage(payload.getBytes());
        msg.setQos(1);
        client.publish(topic, msg);
    }

    public void close() {
        try {
            client.disconnect();
        } catch (MqttException ignored) {}
    }
}
