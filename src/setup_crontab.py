from __future__ import annotations

import logging
import json
from datetime import datetime, timedelta
from random import randint

from crontab import CronItem, CronTab

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.journaling import Journal
from timeio.typehints import MqttPayload

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
        self.configdb_dsn = get_envvar("CONFIGDB_DSN")

    def act(self, content: MqttPayload.ConfigDBUpdate, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.configdb_dsn)
        with CronTab(tabfile=self.tabfile) as crontab:
            for job in crontab:
                if self.job_belongs_to_thing(job, thing):
                    logger.info(f"Updating cronjob for thing {thing.name}")
                    info = self.update_job(job, thing)
                    journal.info(f"Updated cronjob to sync {info}", thing.uuid)
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
        if thing.ext_sftp is not None:
            interval = int(thing.ext_sftp.sync_interval)
            schedule = cls.get_schedule(interval)
            script = "/scripts/sync_sftp.py"
            command = f"{script} {uuid} > $STDOUT 2> $STDERR"
            job.enable(enabled=thing.ext_sftp.sync_enabled)
            job.set_comment(comment, pre_comment=True)
            job.setall(schedule)
            job.set_command(command)
            info = f"sFTP {thing.ext_sftp.uri} @ {interval}m and schedule {schedule}"
        if thing.ext_api is not None:
            interval = int(thing.ext_api.sync_interval)
            schedule = cls.get_schedule(interval)
            script = "/scripts/mqtt_sync_wrapper.py"
            command = f"python3 {script} {uuid} > $STDOUT 2> $STDERR"
            job.enable(enabled=thing.ext_api.sync_enabled)
            job.set_comment(comment, pre_comment=True)
            job.setall(schedule)
            job.set_command(command)
            info = f"{thing.ext_api.api_type_name}-API @ {interval}m and schedule {schedule}"
        return info

    @classmethod
    def update_job(cls, job: CronItem, thing: Thing) -> str:
        info = ""
        comment = cls.mk_comment(thing)
        uuid = thing.uuid
        current_interval = cls.get_current_interval(job)
        if thing.ext_sftp is not None:
            new_interval = int(thing.ext_sftp.sync_interval)
            script = "/scripts/sync_sftp.py"
            command = f"{script} {uuid} > $STDOUT 2> $STDERR"
            job.enable(enabled=thing.ext_sftp.enabled)
            job.set_comment(comment, pre_comment=True)
            # if the interval has changed we want to ensure consistent starting times with the previous one
            if current_interval != new_interval:
                schedule = cls.update_cron_expression(job, new_interval)
            else:
                schedule = str(job.slices)
            job.setall(schedule)
            job.set_command(command)
            info = (
                f"sFTP {thing.ext_sftp.uri} @ {new_interval}m and schedule {schedule}"
            )
        elif thing.ext_api is not None:
            new_interval = int(thing.ext_api.sync_interval)
            # if the interval has changed we want to ensure consistent starting dates
            if current_interval != new_interval:
                schedule = cls.update_cron_expression(job, new_interval)
            else:
                schedule = str(job.slices)
            script = "/scripts/mqtt_sync_wrapper.py"
            command = f"python3 {script} {uuid} > $STDOUT 2> $STDERR"
            job.enable(enabled=thing.ext_api.enabled)
            job.set_comment(comment, pre_comment=True)
            job.setall(schedule)
            job.set_command(command)
            info = f"{thing.ext_api.api_type_name}-API @ {new_interval}m and schedule {schedule}"
        return info

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

    @staticmethod
    def get_current_interval(job: CronItem) -> int:
        """Get interval in minutes from crontab.txt entry"""
        schedule = job.schedule()
        next_run = schedule.get_next()
        prev_run = schedule.get_prev()
        interval = next_run - prev_run
        return int(interval.seconds / 60)

    @staticmethod
    def extract_base_minute(schedule: str) -> int:
        """Extract the minute value from the cron expression. In the case
        of multiple values, the first one is returned.
        """
        minute_part = schedule.split()[0]
        if "," in minute_part:
            return int(minute_part.split(",")[0])
        elif minute_part.isdigit():
            return int(minute_part)
        return 0

    @classmethod
    def update_cron_expression(cls, job, new_interval: int) -> str:
        """Update cron while keeping the same base minute for consistency."""
        base_minute = cls.extract_base_minute(str(job.slices))
        if new_interval < 60:
            minutes = sorted(
                (base_minute + i * new_interval) % 60 for i in range(60 // new_interval)
            )
            return f"{','.join(map(str, minutes))} * * * *"

        elif new_interval < 1440:
            return f"{base_minute} */{new_interval // 60} * * *"

        else:
            return f"{base_minute} 0 */{new_interval // 1440} * *"


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInCrontabHandler().run_loop()
