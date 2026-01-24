#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest

from timeio import feta
from timeio.databases import Database
from timeio.qc.utils import collect_tests


@pytest.fixture(scope="session")
def feta_project():
    db = Database("postgresql://postgres:postgres@localhost/postgres")
    with db.connection() as conn:
        yield feta.Project.from_uuid("00000000-0000-0000-0000-000000000001", dsn=conn)


def test_collect_tests(feta_project):
    tests = collect_tests(feta_project.get_default_qaqc())
    for t in tests:
        print(t)
