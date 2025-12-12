commit a4ab20b29c75f281e0546efda3a19444fd19aeee
Author: Joost Hemmen <joost.hemmen@ufz.de>
Date:   Fri Dec 12 23:10:09 2025 +0100

    fix mqtt setup and update dockercompose dev example

diff --git a/src/setup_mqtt_user.py b/src/setup_mqtt_user.py
index a0b9115..f635a1c 100755
--- a/src/setup_mqtt_user.py
+++ b/src/setup_mqtt_user.py
@@ -7,6 +7,7 @@ import psycopg
 
 from timeio.mqtt import AbstractHandler, MQTTMessage
 from timeio.feta import Thing
+from timeio.databases import ReentrantConnection
 from timeio.common import get_envvar, setup_logging
 from timeio.journaling import Journal
 from timeio.typehints import MqttPayload
@@ -26,10 +27,13 @@ class CreateMqttUserHandler(AbstractHandler):
             mqtt_qos=get_envvar("MQTT_QOS", cast_to=int),
             mqtt_clean_session=get_envvar("MQTT_CLEAN_SESSION", cast_to=bool),
         )
-        self.db = psycopg.connect(get_envvar("DATABASE_URL"))
+        self.db_conn = ReentrantConnection(get_envvar("DATABASE_URL"))
+        self.db = self.db_conn.connect()
         self.configdb_dsn = get_envvar("CONFIGDB_DSN")
 
     def act(self, content: MqttPayload.ConfigDBUpdate, message: MQTTMessage):
+        self.db = self.db_conn.connect()   
+
         thing = Thing.from_uuid(content["thing"], dsn=self.configdb_dsn)
         user = thing.mqtt.user
         pw = thing.mqtt.password_hashed
