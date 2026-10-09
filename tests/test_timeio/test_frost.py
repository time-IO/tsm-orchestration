#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET  # noqa

import pytest
from cryptography.fernet import Fernet
from timeio import frost
from timeio.crypto import encrypt

SCHEMA = "myproject"
PASSWORD = "s3cret"
DB_URL = "postgresql://db.example.org:5432/postgres"
PROXY_URL = "https://tsm.example.org/sta/"


@pytest.fixture(scope="module", autouse=True)
def create_secret():
    """Create a new Fernet key, see test_crypto.py for the reasoning."""
    os.environ["FERNET_ENCRYPTION_SECRET"] = Fernet.generate_key().decode()


def write_and_parse(tmp_path, user, **kwargs) -> ET.Element:
    frost.write_context_file(
        schema=SCHEMA,
        user=user,
        password=encrypt(PASSWORD, os.environ["FERNET_ENCRYPTION_SECRET"]),
        db_url=DB_URL,
        tomcat_proxy_url=PROXY_URL,
        context_dir=tmp_path,
        **kwargs,
    )
    return ET.parse(tmp_path / f"{SCHEMA}.xml").getroot()


@pytest.mark.parametrize("user", ["sta_ro_myproject", "sti_ro_myproject"])
def test_write_context_file(tmp_path, user):
    context = write_and_parse(tmp_path, user)

    assert context.get("path") == f"/{SCHEMA}"
    params = {p.get("name"): p.get("value") for p in context.iter("Parameter")}
    assert params["serviceRootUrl"] == f"{PROXY_URL}{SCHEMA}"

    resource = context.find("Resource")
    assert resource.get("username") == user
    assert resource.get("password") == PASSWORD
    assert resource.get("url") == "jdbc:postgresql://db.example.org:5432/postgres"


def test_internal_context_differs_from_public_only_by_user(tmp_path):
    public, internal = tmp_path / "public", tmp_path / "internal"
    public.mkdir(), internal.mkdir()

    pub = write_and_parse(public, "sta_ro_myproject")
    int_ = write_and_parse(internal, "sti_ro_myproject")

    int_.find("Resource").set("username", "sta_ro_myproject")
    assert ET.tostring(pub) == ET.tostring(int_)


def test_context_dirs_are_distinct():
    assert frost.INTERNAL_CONTEXT_FILES_DIR != frost.CONTEXT_FILES_DIR
    assert frost.INTERNAL_CONTEXT_FILES_DIR.name == "frost_context_files_internal"
