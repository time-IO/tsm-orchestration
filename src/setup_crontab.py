from __future__ import annotations

import logging
import json
from datetime import datetime, timedelta
from random import randint

from crontab import CronItem, CronTab, CronRange, CronSlices

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
                    info = self.apply_job(job, thing, is_new=False)
                    journal.info(f"Updated cronjob to sync {info}", thing.uuid)
                    return
            # if no job was found, create a new one
            job = crontab.new()
            logger.info(f"Creating job for thing {thing.name}")
            info = self.apply_job(job, thing, is_new=True)
            if not info:
                logger.warning(
                    "no Cronjob was created, because neither extAPI, "
                    "nor extSFTP is present"
                )
                return
            crontab.append(job)
            journal.info(f"Created cronjob to sync {info}", thing.uuid)

    @classmethod
    def apply_job(cls, job: CronItem, thing: Thing, is_new: bool = True) -> str:
        """Create or update a cron job for `thing`.
        If `is_new` is True the schedule is generated with `get_schedule`,
        otherwise it is adapted with `update_cron_expression`.
        Returns info string (or empty if nothing to do).
        """
        comment = cls.mk_comment(thing)
        uuid = thing.uuid
        script = "/scripts/mqtt_sync_wrapper.py"
        command = f"python3 {script} sync-thing {uuid} > $STDOUT 2> $STDERR"
        if thing.ext_sftp:
            interval = int(thing.ext_sftp.sync_interval)
            schedule = (
                cls.get_schedule(interval)
                if is_new
                else cls.update_cron_expression(job, interval)
            )
            job.enable(enabled=thing.ext_sftp.sync_enabled)
            info = f"sFTP {thing.ext_sftp.uri} @ {interval}m and schedule {schedule}"
        elif thing.ext_api:
            interval = int(thing.ext_api.sync_interval)
            schedule = (
                cls.get_schedule(interval)
                if is_new
                else cls.update_cron_expression(job, interval)
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

    @staticmethod
    def new_base_minute(interval: int) -> int:
        if interval == 0:
            return 0
        return randint(0, min(interval - 1, 59))

    @staticmethod
    def new_base_hour(interval: int) -> int:
        if interval < 60:
            return 0
        return randint(0, min(interval // 60 - 1, 23))

    @staticmethod
    def new_base_dom(interval: int) -> int:
        if interval < 1440:
            return 0
        return randint(0, min(interval // 1440 - 1, 30))

    @classmethod
    def get_schedule(cls, interval: int) -> str:
        # set a random delay to avoid all jobs running at the same time
        # maximum delay is the interval or 59, whichever is smaller
        delay_m = cls.new_base_minute(interval)
        # interval is smaller than an hour
        if interval < 60:
            step_minutes = interval
            return f"{delay_m}-59/{step_minutes} * * * *"
        delay_h = cls.new_base_hour(interval)
        # interval is smaller than a day
        if interval < 1440:
            delay_h = cls.new_base_hour(interval)
            step_hours = interval // 60
            return f"{delay_m} {delay_h}-23/{step_hours} * * *"
        # interval is exactly weekly
        elif interval == 10080:
            delay_dow = randint(0, 6)
            return f"{delay_m} {delay_h} * * {delay_dow}"
        # interval is larger than a day but not weekly
        else:
            delay_dom = cls.new_base_dom(interval)
            step_days = interval // 1440
            return f"{delay_m} {delay_h} {delay_dom}-31/{step_days} * *"

    @staticmethod
    def get_current_interval(job: CronItem) -> int:
        """Get interval in minutes from crontab.txt entry"""
        # TODO:
        #  This is not reliable to extract the interval.
        #  because if we have a 40 min schedule (5-59/40 * * * *)
        #  and current time is 12:00, get_last returns 11:45 and get_next returns 12:05
        #  which results in an interval of 20 minutes.
        #  In contrast if current time is 12:30, get_last returns 12:05 and get_next
        #  returns 12:45 which results in an interval of 40 minutes.
        schedule = job.schedule()
        next_run = schedule.get_next()
        prev_run = schedule.get_prev()
        interval = next_run - prev_run
        return int(interval.total_seconds() / 60)

    @staticmethod
    def extract_base_minute(schedule: str | CronSlices) -> int | None:
        """Extract the minute value from the cron expression.
        Handles comma lists, ranges with step (e.g. '7-59/10'), '*' with step (e.g. '*/15'), etc.
        Returns the first numeric start value or 0 on parse failure.
        """
        if isinstance(schedule, CronSlices):
            schedule = schedule.render()
        minutes = schedule.split()[0]  # split along spaces and take minutes part
        minutes = minutes.split(",")[0]  # rm possible list of values
        minutes = minutes.split("/")[0]  # rm possible step value
        minutes = minutes.split("-")[0]  # rm possible ranges value
        if minutes == "*" or minutes[0] == "@":
            return 0
        try:
            return int(minutes)
        except ValueError:
            return None

    @staticmethod
    def extract_base_hour(schedule: str) -> int | None:
        """Extract the hour value from the cron expression.
        Handles comma lists, ranges with step (e.g. '7-24/10'), '*' with step (e.g. '*/15'), etc.
        Returns the first numeric start value or 0 on parse failure.
        """
        if isinstance(schedule, CronSlices):
            schedule = schedule.render()
        parts = schedule.split()
        if len(parts) == 1:
            return None
        hour = parts[1]
        hour = hour.split(",")[0]  # rm possible list of values
        hour = hour.split("/")[0]  # rm possible step value
        hour = hour.split("-")[0]  # rm possible ranges value
        if hour == "*" or hour[0] == "@":
            return 0
        try:
            return int(hour)
        except ValueError:
            return None

    @classmethod
    def update_cron_expression(cls, job, new_interval: int) -> str:
        """Update cron while keeping the same base minute for consistency.
        If the existing schedule already encodes the requested periodicity
        (produced by `get_schedule`, e.g. contains '/{step}', range-with-step
        or a matching comma-list for minutes), return the original string unchanged.
        """
        current_interval = cls.get_current_interval(job)
        original = str(job.slices)
        # TODO: see comment in get_current_interval, maybe we should save the interval
        #  somewhere relivable for example within the job.comment ?
        if current_interval == new_interval:
            return original

        base_minute = cls.extract_base_minute(original) or cls.new_base_minute(
            new_interval
        )
        base_hour = cls.extract_base_hour(original) or cls.new_base_hour(new_interval)

        # interval below 60 minutes
        if new_interval < 60:
            if base_minute >= new_interval:
                base_minute = cls.new_base_minute(new_interval)
            return f"{base_minute}-59/{new_interval} * * * *"

        # interval between one hour and a day
        elif new_interval < 1440:
            hour_step = new_interval // 60
            return f"{base_minute} */{hour_step} * * *"

        elif new_interval == 10080:
            dow = randint(0, 6)
            return f"{base_minute} {base_hour} * * {dow}"

        else:  # new_interval > 10080
            return f"{base_minute} {base_hour} */{new_interval // 1440} * *"


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInCrontabHandler().run_loop()
