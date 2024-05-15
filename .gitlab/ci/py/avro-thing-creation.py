#!/usr/bin/env python3

import time
import json
import paho.mqtt.client as mqtt
import fastavro
import threading
import os
import sys

# MQTT settings
host = "docker"
port = 1883
topic = "thing_creation"
username = "mqtt"
password = "mqtt"
qos = 0


def on_connect(client, userdata, flags, rc):
    print(f"Connected to broker with result code {rc}")
    client.subscribe(topic, qos)
    with lock:
        global connected
        connected = True

def on_message(client, userdata, msg):
    global is_valid
    print(msg.topic + " " + str(msg.payload))
    msg_json = json.loads(msg.payload)
    if validate_message(msg_json):
        is_valid = True

def validate_message(msg_json):
    avsc_file = "./.gitlab/ci/avsc/thing_creation.avsc"
    if not os.path.isfile(avsc_file):
        print(f"Avro schema file {avsc_file} not found")
        return
    print("Validating message...")
    try:
        schema = fastavro.schema.load_schema(avsc_file)
        fastavro.validate(msg_json, schema)
        print("Message valid")
        return True
    except Exception as e:
        print(f"Message not valid. Returning exception:\n{e}")
        return False

def django_loaddata():
    print("Loading Django fixtures")
    os.system(
        "docker compose exec -T frontend2 python3 manage.py loaddata user.json > /dev/null 2>&1"
    )
    time.sleep(2)
    os.system(
        "docker compose exec -T frontend2 python3 manage.py loaddata thing.json > /dev/null 2>&1"
    )
    time.sleep(2)

def build_client():
    clt = mqtt.Client()
    clt.on_connect = on_connect
    clt.on_message = on_message
    clt.username_pw_set(username, password)
    return clt

def connect_and_listen():
    client = build_client()
    client.connect(host, port)
    client.loop_start()
    start_time = time.time()
    while not is_valid and time.time() - start_time < 30:
        time.sleep(1)
    time.sleep(2)
    client.disconnect()


if __name__ == "__main__":
    is_valid = False
    connected = False
    lock = threading.Lock()
    t1 = threading.Thread(target=connect_and_listen)
    t1.start()
    while not connected:
        time.sleep(1)
    django_loaddata()
    t1.join()
    if is_valid:
        print("Success!")
        sys.exit(0)
    else:
        print("Failed!")
        sys.exit(1)
