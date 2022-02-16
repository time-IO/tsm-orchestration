import os
import ast
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("thing_created")


def on_message(client, userdata, message):
    content = str(message.payload.decode("utf-8"))
    parsed_content = ast.literal_eval(content)
    print("Received message on topic '{topic}' with QoS {qos}:".format(topic=message.topic, qos=message.qos))
    print(parsed_content)
    # print(message.mid)

def on_log(client, userdata, level, buf):
    print("log: ", buf)

mqtt_broker = os.environ.get("MQTT_BROKER")
mqtt_user = os.environ.get("MQTT_USER")
mqtt_password = os.environ.get("MQTT_PASSWORD")

client = mqtt.Client()
client.username_pw_set(mqtt_user, mqtt_password)
client.on_connect = on_connect
client.on_message = on_message
client.on_log = on_log
client.connect(mqtt_broker, 1883, 60)

client.loop_forever()

