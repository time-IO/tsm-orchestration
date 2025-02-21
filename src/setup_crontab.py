from __future__ import annotations

import logging
from datetime import datetime
from random import randint

from crontab import CronItem, CronTab

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.thing import Thing
from timeio.common import get_envvar, setup_logging
from timeio.journaling import Journal

logger = logging.getLogger("crontab-setup")
journal = Journal("Cron")


class CreateThingInCrontabHandler(AbstractHandler):
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
        self.tabfile = "/tmp/cron/crontab.txt"

    def act(self, content: dict, message: MQTTMessage):
        thing = Thing.get_instance(content)
        with CronTab(tabfile=self.tabfile) as crontab:
            for job in crontab:
                if self.job_belongs_to_thing(job, thing):
                    logger.info(f"Updating cronjob for thing {thing.name}")
                    self.update_job(job, thing)
                    journal.info(f"Updated cronjob", thing.uuid)
                    return
            # if no job was found, create a new one
            job = crontab.new()
            logger.info(f"Creating job for thing {thing.name}")
            info = self.make_job(job, thing)
            if not info:
                logger.warning(
                    "no Cronjob was created, because neither extAPI, "
                    "nor extSFTP is present"
                )
                return
            crontab.append(job)
            journal.info(f"Created cronjob to sync {info}", thing.uuid)

    @classmethod
    def make_job(cls, job: CronItem, thing: Thing) -> str:
        info = ""
        comment = cls.mk_comment(thing)
        uuid = thing.uuid
        if thing.external_sftp is not None:
            interval = int(thing.external_sftp.sync_interval)
            schedule = cls.get_schedule(interval)
            script = "/scripts/sync_sftp.py"
            keyfile = thing.external_sftp.private_key_path
            command = f"{script} {uuid} {keyfile} > $STDOUT 2> $STDERR"
            job.enable(enabled=thing.external_sftp.enabled)
            job.set_comment(comment, pre_comment=True)
            job.setall(schedule)
            job.set_command(command)
            info = f"sFTP {thing.external_sftp.uri} @ {interval}s"
        if thing.external_api is not None:
            interval = int(thing.external_api.sync_interval)
            schedule = cls.get_schedule(interval)
            script = f"/scripts/sync_{thing.external_api.api_type_name}_api.py"
            target_uri = thing.database.url
            command = f"""{script} {uuid} "{thing.external_api.settings}" {target_uri} > $STDOUT 2> $STDERR"""
            job.enable(enabled=thing.external_api.enabled)
            job.set_comment(comment, pre_comment=True)
            job.setall(schedule)
            job.set_command(command)
            info = f"{thing.external_api.api_type_name}-API @ {interval}s"
        return info

    # alias
    update_job = make_job

    @staticmethod
    def job_belongs_to_thing(job: CronItem, thing: Thing) -> bool:
        """Check if job belongs to thing."""
        return job.comment.split(" | ")[-1] == thing.uuid

    @staticmethod
    def mk_comment(thing: Thing) -> str:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{now_str} | {thing.project.name} | {thing.name} | {thing.uuid}"

    @staticmethod
    def get_schedule(interval: int) -> str:
        # set a random delay to avoid all jobs running at the same time
        # maximum delay is the interval or 59, whichever is smaller
        delay_m = randint(0, min(interval - 1, 59))
        # interval is smaller than an hour
        if interval < 60:
            return f"{delay_m}-59/{interval} * * * *"
        # interval is smaller than a day
        elif interval < 1440:
            delay_h = randint(0, min(interval // 60 - 1, 23))
            return f"{delay_m} {delay_h}-23/{interval//60} * * *"
        else:
            delay_h = randint(0, min(interval // 60 - 1, 23))
            delay_wd = randint(0, min(interval // 1440 - 1, 6))
            return f"{delay_m} {delay_h} * * {delay_wd}-6/{interval//1440}"


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInCrontabHandler().run_loop()
