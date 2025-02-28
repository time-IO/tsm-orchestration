#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import json

from datetime import datetime, timedelta, timezone


from timeio.mqtt import publish_single
from timeio.feta import Thing
from timeio.common import get_envvar


def get_tsytsems_timerange():
    now_utc = datetime.now(timezone.utc)
    now_str = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    timestamp_from = now_utc - timedelta(minutes=60)
    timestamp_from_str = timestamp_from.strftime("%Y-%m-%dT%H:%M:%SZ")
    return timestamp_from_str, now_str


def get_dwd_timerange():
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_start = datetime.strftime(yesterday, "%Y-%m-%d:00:00:00")
    yesterday_end = datetime.strftime(yesterday, "%Y-%m-%d:23:55:00")
    return yesterday_start, yesterday_end


TIMERANGE_MAPPING = {"tsystems": get_tsytsems_timerange(), "dwd": get_dwd_timerange()}


@click.command()
@click.argument("thing_uuid")
def main(thing_uuid: str):
    thing = Thing.from_uuid(thing_uuid, dsn=get_envvar("CONFIGDB_DSN"))
    ext_api_name = thing.ext_api.api_type_name
    datetime_from, datetime_to = TIMERANGE_MAPPING[ext_api_name]
    message = {
        "thing": thing.uuid,
        "datetime_from": datetime_from,
        "datetime_to": datetime_to,
    }
    publish_single(
        f"sync_ext_apis/{ext_api_name}", json.dumps(message)
    )


if __name__ == "__main__":
    main()
