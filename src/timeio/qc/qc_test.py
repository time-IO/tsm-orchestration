#!/usr/bin/env python3
import pandas as pd
import saqc


class QcTest:
    nr: int
    name: str
    description: str

    def load_data(self) -> pd.DataFrame:
        ...

    def run(self, qc: saqc.SaQC) -> saqc.SaQC:
        ...