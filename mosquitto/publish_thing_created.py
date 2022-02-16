import os
import time
import paho.mqtt.client as mqtt
import avro.schema
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter

database = {
    "username": "myfirstproject_6185a5b8462711ec910a125e5a40a845",
    "password": "d0ZZ9d3QSDZ6tXIZTnKRY1uVLKIc05GmQh8SA36M",
    "url": "postgresql://myfirstproject_6185a5b8462711ec910a125e5a40a845:d0ZZ9d3QSDZ6tXIZTnKRY1uVLKIc05GmQh8SA36M@postgres/postgres"
}

project = {
    "name": "My first project",
    "uuid": "6185a5b8-4627-11ec-910a-125e5a40a845"
}

raw_data_storage = {
    "bucket_name": "thedoors-057d8bba-40b3-11ec-a337-125e5a40a849",
    "username": "thedoors-057d8bba-40b3-11ec-a337-125e5a40a849",
    "password": "R3eKIIxZWtYlC9s9ZIEeWc4peH4OebiHWE252xQF"
}

parser = {
    "settings": {
        "timestamp_format": "%Y/%m/%d %H:%M:%S",
        "header": 3,
        "delimiter": ",",
        "timestamp_column": 1,
        "skipfooter": 1
    }
}

event = {
    "uuid": "057d8bba-40b3-11ec-a337-125e5a40a849",
    "name": "The Doors",
    "database": database,
    "project": project,
    "raw_data_storage": raw_data_storage,
    "parser": parser
}

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

def on_publish(client, userdata, mid):
    print("Message with mid: {} published.".format(mid))

### Change path to the current .avsc location!!!
schema = avro.schema.parse(open("thing_event.avsc", "rb").read())

with DataFileWriter(open("thing_event.avro", "wb"), DatumWriter(), schema) as writer:
    writer.append(event)

mqtt_broker = os.environ.get("MQTT_BROKER")
mqtt_user = os.environ.get("MQTT_USER")
mqtt_password = os.environ.get("MQTT_PASSWORD")

reader = DataFileReader(open("thing_event.avro", "rb"), DatumReader())
client = mqtt.Client("thing")
client.username_pw_set(mqtt_user, mqtt_password)
client.connect(mqtt_broker,1883,60)
client.on_connect = on_connect
client.on_publish = on_publish
client.loop_start()
for user in reader:
    client.publish("thing_created", str(user), qos=2,retain=False)
    time.sleep(1)
    client.loop_stop()
reader.close()
