from __future__ import annotations

import logging
from datetime import datetime
from random import randint

from crontab import CronItem, CronTab

from timeio.cron import (
    SYNC_JITTER_SECONDS,
    build_command,
    jitter_from_command,
    new_schedule,
    update_cron_expression,
)
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
        self.dsmdb_dsn = get_envvar("DSMDB_DSN")

    def act(self, content: MqttPayload.UpdateThing, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.dsmdb_dsn)
        with CronTab(tabfile=self.tabfile) as crontab:
            job = next(
                (j for j in crontab if self.job_belongs_to_thing(j, thing)), None
            )
            is_new = job is None
            if is_new:
                job = crontab.new()
            logger.info(
                f"{'Creating' if is_new else 'Updating'} cronjob for thing {thing.name}"
            )
            info = self.apply_job(job, thing, is_new=is_new)
            if not info:
                if is_new:
                    logger.warning(
                        "no Cronjob was created, because neither extAPI, "
                        "nor extSFTP is present"
                    )
                else:
                    crontab.remove(job)
                    journal.info(
                        "Removed cronjob, no external sync configured", thing.uuid
                    )
            else:
                if is_new:
                    crontab.append(job)
                journal.info(
                    f"{'Created' if is_new else 'Updated'} cronjob to sync {info}",
                    thing.uuid,
                )

    @classmethod
    def apply_job(cls, job: CronItem, thing: Thing, is_new: bool = True) -> str:
        """Create or update a cron job for `thing`.
        If `is_new` is True the schedule is generated with `new_schedule`,
        otherwise it is adapted with `update_cron_expression`.
        Returns info string (or empty if nothing to do).
        """
        comment = cls.mk_comment(thing)
        uuid = thing.uuid
        offset = None if is_new else jitter_from_command(job.command)
        if offset is None:
            offset = randint(0, SYNC_JITTER_SECONDS)
        command = build_command("sync_thing", uuid, None, offset)
        if thing.ext_sftp:
            interval = int(thing.ext_sftp.sync_interval)
            schedule = (
                new_schedule(interval)
                if is_new
                else update_cron_expression(str(job.slices), interval)
            )
            job.enable(enabled=thing.ext_sftp.sync_enabled)
            info = f"sFTP {thing.ext_sftp.uri} @ {interval}m and schedule {schedule}"
        elif thing.ext_api:
            interval = int(thing.ext_api.sync_interval)
            schedule = (
                new_schedule(interval)
                if is_new
                else update_cron_expression(str(job.slices), interval)
            )
            job.enable(enabled=thing.ext_api.enabled)
            info = f"{thing.ext_api.api_type_name}-API @ {interval}m and schedule {schedule}"
        else:
            return ""
        job.set_comment(comment, pre_comment=True)
        job.set_command(command)
        job.setall(schedule)
        return info

    @staticmethod
    def job_belongs_to_thing(job: CronItem, thing: Thing) -> bool:
        """Check if job belongs to thing."""
        return job.comment.split(" | ")[-1] == thing.uuid

    @staticmethod
    def mk_comment(thing: Thing) -> str:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{now_str} | {thing.project.name} | {thing.name} | {thing.uuid}"


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInCrontabHandler().run_loop()
