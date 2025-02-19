from __future__ import annotations

import logging

from minio_cli_wrapper.mc import Mc

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.crypto import decrypt, get_crypt_key
from timeio.typehints import MqttPayload

logger = logging.getLogger("minio-setup")


class CreateThingInMinioHandler(AbstractHandler):
    def __init__(self):
        super().__init__(
            topic=get_envvar("TOPIC"),
            mqtt_broker=get_envvar("MQTT_BROKER"),
            mqtt_user=get_envvar("MQTT_USER"),
            mqtt_password=get_envvar("MQTT_PASSWORD"),
            mqtt_client_id=get_envvar("MQTT_CLIENT_ID"),
            mqtt_qos=get_envvar("MQTT_QOS", cast_to=int),
            mqtt_clean_session=get_envvar("MQTT_CLEAN_SESSION", cast_to=bool),
        )
        # Custom minio client wrapper
        self.mcw = Mc(
            url=get_envvar("MINIO_URL"),
            access_key=get_envvar("MINIO_ACCESS_KEY"),
            secret_key=get_envvar("MINIO_SECURE_KEY"),
            secure=get_envvar("MINIO_SECURE", default=True, cast_to=bool),
        )

    def act(self, content: MqttPayload.ConfigDBUpdate, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"])
        user = thing.raw_data_storage.username
        passw = decrypt(thing.raw_data_storage.password, get_crypt_key())
        bucket = thing.raw_data_storage.bucket_name

        # create user
        # not implemented in minio python sdk yet :(
        # so we have to use minio cli client wrapper
        logger.info("create user")
        self.mcw.user_add(user, passw)

        # mc admin policy add myminio/ datalogger1-policy /root/iam-policy-datalogger1.json
        # not implemented in minio python sdk yet :(
        self.mcw.policy_add(
            user,
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetBucketLocation",
                            "s3:GetObject",
                            "s3:ListBucket",
                            "s3:PutObject",
                        ],
                        "Resource": [
                            f"arn:aws:s3:::{bucket}",
                            f"arn:aws:s3:::{bucket}/*",
                        ],
                    }
                ],
            },
        )

        # mc admin policy set myminio/ datalogger1-policy user=datalogger1-user
        # not implemented in minio python sdk yet :(
        self.mcw.policy_set_user(user, user)

        # Create bucket
        if self.mcw.bucket_exists(bucket):
            logger.info(f"bucket {bucket} already exists")
        else:
            logger.info(f"create bucket {bucket}")
            try:
                self.mcw.make_locked_bucket(bucket)
            except Exception as e:
                raise ValueError(f'Unable to create bucket "{bucket}"') from e

        self.mcw.set_bucket_100y_retention(bucket)
        self.mcw.enable_bucket_notification(bucket)
        logger.info("store bucket metadata (db connection, thing uuid, etc.)")


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInMinioHandler().run_loop()
