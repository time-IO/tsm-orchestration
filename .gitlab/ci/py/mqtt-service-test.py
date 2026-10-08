#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import random
import string
import sys
import os
import threading
import time

# MQTT settings
host = os.environ.get("MQTT_SERVICE_TEST_HOST", "docker")
port = 1883
qos = 0
# Seconds to keep retrying the first connection and to wait for the message
connect_timeout = 60
receive_timeout = 30

done = threading.Event()


def generate_random_user():
    return "".join(random.choice(string.ascii_letters) for _ in range(5))


def generate_random_password():
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(10)
    )


def generate_random_topic(username):
    return f"mqtt_ingest/{username}/" + "/".join(
        "".join(random.choice(string.ascii_letters) for _ in range(5)) for _ in range(2)
    )


def set_mosquitto_password(user, passwd):
    os.system(
        f"docker compose exec -T mqtt-broker bash -c 'echo {user}:$(/mosquitto/pw -p {passwd}) >> /tmp/mosquitto/auth/mosquitto.passwd'"
    )
    # `restart` returns before the broker accepts connections again. Wait for
    # its healthcheck (an authenticated subscribe) instead of a fixed sleep.
    exit_code = os.system(
        "echo Restarting mqtt-broker; docker compose restart mqtt-broker > /dev/null 2>&1; "
        "docker compose up -d --no-deps --wait --wait-timeout 120 mqtt-broker > /dev/null 2>&1"
    )
    if exit_code != 0:
        print("mqtt-broker did not become healthy after the restart")
        sys.exit(1)


def generate_random_message():
    random_text = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(20)
    )
    return random_text


def on_connect(client, userdata, flags, rc):
    global topic
    global message
    if rc != 0:
        # Callbacks run in the network thread, where sys.exit() would not end
        # the test; report and let the main thread fail.
        print(f"Failed to connect to broker with result code {rc}")
        done.set()
    else:
        print(f"Connected to broker with result code {rc}")
        client.subscribe(topic, qos)
        print(f"Subscribed to topic: {topic}")
        client.publish(topic, message, qos)
        print(f"Sent message:        {message}")


def on_message(client, userdata, msg):
    global is_received
    global message
    received_message = msg.payload.decode()
    print(f"Received message:    {received_message}")
    if received_message == message:
        is_received = True
    done.set()


def connect_and_listen():
    global username
    global password
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(username=username, password=password)
    deadline = time.monotonic() + connect_timeout
    while True:
        try:
            client.connect(host, port)
            break
        except OSError as e:
            if time.monotonic() >= deadline:
                print(
                    f"Could not connect to {host}:{port} within {connect_timeout}s: {e}"
                )
                sys.exit(1)
            time.sleep(2)
    client.loop_start()
    if not done.wait(receive_timeout):
        print(f"No message received within {receive_timeout}s")
    client.disconnect()
    client.loop_stop()


if __name__ == "__main__":
    is_received = False
    username = generate_random_user()
    print(f"Generated user:      {username}")
    password = generate_random_password()
    print(f"Generated password:  {password}")
    set_mosquitto_password(username, password)
    message = generate_random_message()
    topic = generate_random_topic(username)
    print(f"Generated topic:     {topic}")
    connect_and_listen()
    if is_received:
        print("Success!")
        sys.exit(0)
    else:
        print("Failed!")
        sys.exit(1)
