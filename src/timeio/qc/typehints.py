#!/usr/bin/env python3
from __future__ import annotations
import typing
import datetime

if typing.TYPE_CHECKING:
    import pandas as pd
    from pandas._libs.tslibs.nattype import NaTType

    TimestampT = datetime.datetime | pd.Timestamp | NaTType
    WindowT = int | pd.Timedelta
