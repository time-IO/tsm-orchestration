#!/usr/bin/env python3
from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    import datetime
    import pandas as pd

TimestampT = datetime.datetime.timestamp | pd.Timestamp
WindowT = int | pd.Timedelta
