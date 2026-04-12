#!/usr/bin/env python3
from __future__ import annotations
import datetime
import typing

if typing.TYPE_CHECKING:
    import pandas as pd
    WindowT = int | pd.Timedelta
    TimestampT = datetime.datetime | pd.Timestamp
