package com.timeio.mqtt;

import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.container.ContainerResponseContext;
import jakarta.ws.rs.container.ContainerResponseFilter;
import jakarta.ws.rs.ext.Provider;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.jboss.logging.Logger;

import java.io.IOException;

@Provider
public class UserInfoResponseFilter implements ContainerResponseFilter {

    private static final Logger LOG = Logger.getLogger(UserInfoResponseFilter.class);

    // Hardcodierte MQTT-Settings
    private static final String MQTT_BROKER = "tcp://mqtt-broker:1883";
    private static final String MQTT_USER = "mqtt";
    private static final String MQTT_PASSWORD = "mqtt";
    private static final String MQTT_TOPIC = "user_login";

    private MqttClient mqttClient;

    public UserInfoResponseFilter() {
        try {
            mqttClient = new MqttClient(MQTT_BROKER, MqttClient.generateClientId(), new MemoryPersistence());
            MqttConnectOptions options = new MqttConnectOptions();
            options.setUserName(MQTT_USER);
            options.setPassword(MQTT_PASSWORD.toCharArray());
            options.setAutomaticReconnect(true);
            options.setCleanSession(true);

            mqttClient.connect(options);
            LOG.info("=== MQTT-Verbindung hergestellt ===");

        } catch (Exception e) {
            LOG.error("Fehler beim Verbinden mit MQTT-Broker", e);
        }
    }

    @Override
    public void filter(ContainerRequestContext requestContext,
                       ContainerResponseContext responseContext) throws IOException {

        String path = requestContext.getUriInfo().getPath();

        if (path.contains("/protocol/openid-connect/userinfo")) {
            LOG.infof("=== USERINFO RESPONSE ===");
            LOG.infof("Status: %d", responseContext.getStatus());

            Object entity = responseContext.getEntity();
            if (entity != null) {
                String userInfoJson = entity.toString();
                LOG.infof("UserInfo JSON: %s", userInfoJson);

                // MQTT-Publish
                publishToMqtt(userInfoJson);
            } else {
                LOG.warn("UserInfo Response body ist leer");
            }
        }
    }

    private void publishToMqtt(String payload) {
        try {
            if (mqttClient != null && mqttClient.isConnected()) {
                MqttMessage message = new MqttMessage(payload.getBytes());
                message.setQos(1);
                mqttClient.publish(MQTT_TOPIC, message);
                LOG.infof("MQTT-Nachricht gesendet an Topic '%s': %s", MQTT_TOPIC, payload);
            } else {
                LOG.warn("MQTT-Client nicht verbunden, Nachricht nicht gesendet");
            }
        } catch (Exception e) {
            LOG.error("Fehler beim Senden der MQTT-Nachricht", e);
        }
    }
}