#!/usr/bin/env python3
import abc
from typing import Any

import pandas as pd
import saqc


class QcTool(abc.ABC):

    @abc.abstractmethod
    def check_func_name(self, func_name: str) -> None:
        """
        Checks and returns if the function name is a valid
        qc routine and raise an ValueError otherwise.
        """
        ...

    def execute(
        self,
        func_name: str,
        data: dict[str, pd.Series],
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
    ) -> tuple[dict[str, pd.Series], dict[str, pd.Series]]: ...


class Saqc(QcTool):

    def check_func_name(self, func_name: str):
        if not hasattr(saqc.SaQC, func_name):
            raise ValueError(f"Unknown qc routine {func_name} for SaQC")

    def execute(self, func_name: str, data, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}

        qc = saqc.SaQC(data)
        func = getattr(qc, func_name)
        res: saqc.SaQC = func(*args, **kwargs)

        return dict(res.data), dict(res.flags)
