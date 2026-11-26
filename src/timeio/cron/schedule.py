"""Sync schedule generation and validation; imported by the DSM API, keep it DB-free."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from random import randint

from crontab import SPECIALS, CronItem, CronRange, CronSlices

logger = logging.getLogger("cron")

# @hourly, @daily, ... -> 5 fields; @reboot has no schedule and stays invalid
MACROS = {f"@{k}": v for k, v in SPECIALS.items() if k != "reboot"}

MINUTES_PER_HOUR = 60
MINUTES_PER_DAY = 60 * 24
MINUTES_PER_WEEK = 60 * 24 * 7

# Random per-job start delay (seconds) prepended to the sync command to spread
# out jobs that share the same minute
SYNC_JITTER_SECONDS = 30
MAX_JITTER_SECONDS = 59

_YEAR_RE = re.compile(r"^(\*|\d{4}(-\d{4})?)(/\d+)?$")


def new_base_minute(interval: int) -> int:
    if interval == 0:
        return 0
    if 30 < interval < 60:
        # If for example the interval is 40min, we need to ensure
        # it can run twice an hour and therefor the start minute
        # must be lower than 20.
        return randint(0, 60 % interval - 1)
    return randint(0, min(interval - 1, 59))


def new_base_hour(interval: int) -> int:
    if interval < MINUTES_PER_HOUR:
        return 0
    return randint(0, min(interval // MINUTES_PER_HOUR - 1, 23))


def new_base_dom(interval: int) -> int:
    if interval < 2 * MINUTES_PER_DAY:
        return 1
    return randint(1, min(interval // MINUTES_PER_DAY - 1, 28))


def new_schedule(interval: int) -> str:
    """Creates a new schedule with a random start point to avoid that
    all jobs run at the same time.
    """
    interval = adjust_interval(_orig := interval)
    if _orig != interval:
        logger.info(f"adjusted interval form {_orig} minutes to {interval} minutes")

    start_m = new_base_minute(interval)
    if interval < MINUTES_PER_HOUR:
        step_m = interval
        return f"{start_m}-59/{step_m} * * * *"

    start_h = new_base_hour(interval)
    if interval < MINUTES_PER_DAY:
        start_h = new_base_hour(interval)
        step_h = interval // MINUTES_PER_HOUR
        return f"{start_m} {start_h}-23/{step_h} * * *"

    elif interval == MINUTES_PER_WEEK:
        day_of_week = randint(0, 6)
        return f"{start_m} {start_h} * * {day_of_week}"

    # interval is larger than a day but not weekly
    else:
        start_dom = new_base_dom(interval)
        step_day = interval // MINUTES_PER_DAY
        return f"{start_m} {start_h} {start_dom}-31/{step_day} * *"


def get_current_interval(expression: str) -> int:
    """Get interval in minutes from a cron expression"""
    item = CronItem()
    item.setall(expression)
    schedule = item.schedule(datetime(2020, 1, 1, 23, 59, 59))
    # avoid to have one value in the last hour and one in the next,
    # therefore we avoid schedule.get_prev()
    next_run = schedule.get_next()
    after_next_run = schedule.get_next()
    return int((after_next_run - next_run).total_seconds() / 60)


def adjust_interval(interval: int) -> int:
    """Adjust the interval to a value we can process cleanly in a cron schedule."""
    if interval == 0:
        return 1

    # We adjust the interval to proper divisor of 60.
    if interval <= MINUTES_PER_HOUR:
        divisors = [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60]
        return max(d for d in divisors if d <= interval)

    # We adjust the interval to an exact hourly value which
    # also is a proper divisor of 24h (1,2,3,4,6,8,12,24).
    elif interval <= MINUTES_PER_DAY:
        divisors = [60, 120, 180, 240, 360, 480, 720, 1440]
        return max(d for d in divisors if d <= interval)

    # We adjust the interval to exactly a 7-day value if it's close.
    elif MINUTES_PER_WEEK <= interval < MINUTES_PER_DAY * 8:
        return MINUTES_PER_WEEK

    # We adjust the interval to an exact daily value.
    return (interval // MINUTES_PER_DAY) * MINUTES_PER_DAY


def extract_base_minute(expression: str) -> int | None:
    """Extract the minute value from the cron expression.
    Returns the first numeric start value.
    """
    # if we have a list of expressions like 1,2,4-59/5
    # we extract the base minute only from the first one.
    minutes = CronSlices(expression)[0].parts[0]
    if isinstance(minutes, int):
        return minutes
    assert isinstance(minutes, CronRange)
    return minutes.vfrom


def extract_base_hour(expression: str) -> int | None:
    """Extract the hour value from the cron expression.
    Returns the first numeric start value.
    """
    # If we have a list of expressions like 1,2,4-23/5
    # we extract the base hour only from the first one.
    hour = CronSlices(expression)[1].parts[0]
    if isinstance(hour, int):
        return hour
    assert isinstance(hour, CronRange)
    return hour.vfrom


def update_cron_expression(expression: str, interval: int) -> str:
    """Update cron while keeping the same base minute for consistency.
    If the existing schedule already encodes the requested periodicity
    (produced by `new_schedule`, e.g. contains '/{step}', range-with-step
    or a matching comma-list for minutes), return the original string unchanged.
    """
    interval = adjust_interval(_orig := interval)
    if _orig != interval:
        logger.info(f"adjusted interval form {_orig} minutes to {interval} minutes")

    current_interval = get_current_interval(expression)
    if current_interval == interval:
        # clean_render: str() would collapse e.g. "0 * * * *" to "@hourly"
        return CronSlices(normalize_expression(expression)).clean_render()

    base_minute = extract_base_minute(expression)
    base_hour = extract_base_hour(expression)

    if interval < MINUTES_PER_HOUR:
        if base_minute >= interval:
            base_minute = new_base_minute(interval)
        return f"{base_minute}-59/{interval} * * * *"

    elif interval < MINUTES_PER_DAY:
        hour_step = interval // 60
        return f"{base_minute} */{hour_step} * * *"

    elif interval == MINUTES_PER_WEEK:
        dow = randint(0, 6)
        return f"{base_minute} {base_hour} * * {dow}"

    else:  # new_interval > DAY_MINUTES
        day_step = interval // (60 * 24)
        return f"{base_minute} {base_hour} */{day_step} * *"


def normalize_expression(expression: str) -> str:
    """Collapse whitespace and expand a macro like @hourly to its 5 fields."""
    expression = " ".join(expression.split())
    return MACROS.get(expression.lower(), expression)


def validate_expression(expression: str, allow_seconds: bool = False) -> bool:
    """5 fields, or with `allow_seconds` supercronic's 7 (sec min hour dom mon dow year)."""
    fields = expression.split()
    if len(fields) == 5:
        return CronSlices.is_valid(" ".join(fields))
    if allow_seconds and len(fields) == 7:
        # the seconds field has the syntax and range of a minute field
        return (
            CronSlices.is_valid(f"{fields[0]} * * * *")
            and CronSlices.is_valid(" ".join(fields[1:6]))
            and _YEAR_RE.match(fields[6]) is not None
        )
    return False
