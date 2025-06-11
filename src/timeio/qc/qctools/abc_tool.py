#!/usr/bin/env python3
from __future__ import annotations

import abc
from typing import Self, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


class QcTool(abc.ABC):

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Returns the name of the QcTool"""
        ...

    @property
    @abc.abstractmethod
    def version(self) -> str:
        """Returns the version of the QcTool"""
        ...

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
        Returns a dict of datetime index pandas Dataframes.
        Each with at least one column called "quality", which
        holds the QC information. Other columns that are
        evaluated are:
            * 'measure' (str) - name of the function that created the quality label
            * 'userLabel' (str) - user given information string

        See also -> qc.datastream.QUALITY_COLUMNS
        """
        ...

    @abc.abstractmethod
    def get_data(self) -> dict[str, pd.Series]:
        """
        Returns a dict of datetime indexed pandas Series
        containing the data.
        """
        ...
