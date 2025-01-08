#!/usr/bin/env python3
from __future__ import annotations
import requests
import pytest
from environment import *
import docker as docker_sdk


class TestConfigDbConnection:

    # run a test
    # run in container -> docker.run

    def in_container(self):
        # docker
        pass
