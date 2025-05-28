#!/usr/bin/env python3
from __future__ import annotations
import abc
import warnings
from typing import Any, Self

import pandas as pd
import saqc

try:
    import tsm_user_code  # noqa, this registers user functions on SaQC
except ImportError:
    warnings.warn("could not import module 'tsm_user_code'")


def get_qctool(name) -> type[QcTool]:
    tool = {"saqc": Saqc}.get(name)
    if tool is None:
        raise NotImplementedError(f"No QC tool with name {name}")
    return tool


class QcTool(abc.ABC):

    @property
    @abc.abstractmethod
    def columns(self) -> list[str] | pd.Index:
        """
        Property that returns a list of data series names, that
        are currently stored in the QcTool.
        """
        ...

    @abc.abstractmethod
    def check_func_name(self, func_name: str) -> None:
        """
        Checks and returns if the function name is a valid
        qc routine and raise an ValueError otherwise.
        """
        ...

    @abc.abstractmethod
    def add_data(
        self, data: dict[str, pd.Series], quality: dict[str, pd.Series] | None = None
    ):
        """
        Adds data for the next QcTool.execution() call
        """
        ...

    @abc.abstractmethod
    def execute(self, func_name: str, *args, **kwargs) -> Self: ...

    @abc.abstractmethod
    def get_quality(self) -> dict[str, pd.DataFrame]:
        """
        Returns a dict of pandas Dataframes. Each dataframe has
         - a datetime index
         - a column called "quality" holding the QC information
         - optional other columns
        """
        ...

    @abc.abstractmethod
    def get_data(self):
        """
        Returns a dict of pandas Dataframes. Each dataframe has
         - a datetime index
         - a column called "data" holding the QC information
         - optional other columns
        """


class Saqc(QcTool):

    @property
    def columns(self) -> pd.Index:
        return self._qc.columns

    def check_func_name(self, func_name: str):
        if not hasattr(saqc.SaQC, func_name):
            raise ValueError(f"Unknown qc routine {func_name} for SaQC")

    def __init__(self):
        self._qc = saqc.SaQC()

    def add_data(
        self, data: dict[str, pd.Series], quality: dict[str, pd.Series] | None = None
    ):
        if quality is not None:
            raise NotImplementedError("Not supported yet")

        for key, val in data.items():
            self._qc[key] = val

    def execute(self, func_name: str, *args, **kwargs) -> Self:
        qc = self._qc
        func = getattr(qc, func_name)
        self._qc = func(*args, **kwargs)
        return self

    def get_quality(self):
        return dict(self._qc.flags)

    def get_data(self):
        return dict(self._qc.data)
