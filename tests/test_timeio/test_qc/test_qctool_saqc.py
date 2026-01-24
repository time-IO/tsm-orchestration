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


def select_thing_by_name(things, thing_name):
    return [t for t in things  if t.name == thing_name][0]


@pytest.mark.parametrize(
    "thing_name, expected",
    [
        ("StaticThing", ("Static-T1", "Static-T2", "Static-P1", "Dynamic-P1")),
        ("DynamicThing", ("Dynamic-T1", "Dynamic-T2")),
    ],
)
def test_collect_tests(feta_project, thing_name, expected):

    thing = select_thing_by_name(feta_project.get_things(), thing_name)
    tests = collect_tests(feta_project.get_default_qaqc(), thing)

    assert set(set([t.name for t in tests])) == set(expected)

