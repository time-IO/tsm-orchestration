import os

# Force test DB settings - must be set BEFORE any app imports.
# Uses POSTGRES_TEST_* variables to prevent accidental use of dev DB
# when running inside docker compose (which sets POSTGRES_SERVER=api-db).
os.environ["POSTGRES_SERVER"] = os.environ.get("POSTGRES_TEST_SERVER", "localhost")
os.environ["POSTGRES_PORT"] = os.environ.get("POSTGRES_TEST_PORT", "5435")
os.environ["POSTGRES_DB"] = os.environ.get("POSTGRES_TEST_DB", "db_test")
os.environ["POSTGRES_USER"] = os.environ.get("POSTGRES_TEST_USER", "postgres")
os.environ["POSTGRES_PASSWORD"] = os.environ.get("POSTGRES_TEST_PASSWORD", "postgres")

from tests.utils.test_env import setup_test_env

setup_test_env()
import uuid
import pytest
from sqlmodel import Session, select, text
from fastapi.testclient import TestClient
from models import PermissionGroup, User, PermissionGroupUserLink
from models.parser import Parser
from models.parser_detailed import ParserDetailed
from models.database import Database

from main import app
from dependencies import engine, get_current_user
from tests.utils.user_proxy import UserProxy


@pytest.fixture(scope="session", autouse=True)
def base_data():
    """Creates the minimum required base data in the test DB:
    - one permission_group
    - one parser of type 'csv', with a matching parser_detailed row
    - one real user, linked to the permission_group via the link table
    - one database entry for the permission_group (required by
      create_database_if_not_exists)
    Yields the ids so tests can reference them.
    Deletes everything at the end of the session."""
    with Session(engine) as session:
        pg_group = PermissionGroup(
            name=f"TestGroup-{uuid.uuid4()}",
            uuid=str(uuid.uuid4()),
            entitlement=f"urn:test:group:{uuid.uuid4()}",
        )
        session.add(pg_group)
        parser = Parser(parser_type="csv")
        session.add(parser)
        user = User(
            sub=f"testuser-sub-{uuid.uuid4()}",
            username="testuser",
            email="testuser@example.com",
            given_name="Test",
            family_name="User",
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        session.flush()  # need pg_group.id, parser.id, user.id

        parser_detailed = ParserDetailed(
            parser_id=parser.id,
            permission_group_id=pg_group.id,
            name="TestParser",
        )
        session.add(parser_detailed)
        link = PermissionGroupUserLink(
            permission_group_id=pg_group.id,
            user_id=user.id,
        )
        session.add(link)
        database = Database(
            permission_group_id=pg_group.id,
            name="Test Database",
            username="testuser",
            password="testpassword",
            read_only_username="readonly",
            read_only_password="readonlypassword",
            url="postgresql://localhost/test",
            read_only_url="postgresql://localhost/test",
        )
        session.add(database)
        session.commit()
        ids = {
            "permission_group_id": pg_group.id,
            "parser_id": parser.id,
            "user_id": user.id,
            "database_id": database.id,
        }

    # session is closed here - no interference with FastAPI's sessions
    yield ids

    # cleanup in a fresh session - reverse FK order
    with Session(engine) as session:
        if db := session.get(Database, ids["database_id"]):
            session.delete(db)
        if link := session.exec(
            select(PermissionGroupUserLink).where(
                PermissionGroupUserLink.user_id == ids["user_id"]
            )
        ).first():
            session.delete(link)
        if pd := session.exec(
            select(ParserDetailed).where(ParserDetailed.parser_id == ids["parser_id"])
        ).first():
            session.delete(pd)
        if u := session.get(User, ids["user_id"]):
            session.delete(u)
        if p := session.get(Parser, ids["parser_id"]):
            session.delete(p)
        if pg := session.get(PermissionGroup, ids["permission_group_id"]):
            session.delete(pg)
        session.commit()


@pytest.fixture(scope="session")
def other_group_data():
    """Second permission group + user for testing group isolation."""
    with Session(engine) as session:
        pg_group = PermissionGroup(
            name=f"OtherTestGroup-{uuid.uuid4()}",
            uuid=str(uuid.uuid4()),
            entitlement=f"urn:test:group:{uuid.uuid4()}",
        )
        session.add(pg_group)
        other_user = User(
            sub=f"test-sub-other-{uuid.uuid4()}",
            username="otheruser",
            email="otheruser@example.com",
            given_name="Other",
            family_name="User",
            is_active=True,
            is_superuser=False,
        )
        session.add(other_user)
        session.flush()  # need pg_group.id, other_user.id

        link = PermissionGroupUserLink(
            permission_group_id=pg_group.id,
            user_id=other_user.id,
        )
        session.add(link)
        session.commit()
        ids = {"permission_group_id": pg_group.id, "user_id": other_user.id}

    # session is closed here
    yield ids

    # cleanup in a fresh session
    with Session(engine) as session:
        if link := session.exec(
            select(PermissionGroupUserLink).where(
                PermissionGroupUserLink.user_id == ids["user_id"]
            )
        ).first():
            session.delete(link)
        if u := session.get(User, ids["user_id"]):
            session.delete(u)
        if pg := session.get(PermissionGroup, ids["permission_group_id"]):
            session.delete(pg)
        session.commit()


@pytest.fixture
def client(base_data) -> TestClient:
    with Session(engine) as s:
        user = s.get(User, base_data["user_id"])
        proxy = UserProxy(user, [base_data["permission_group_id"]])
    app.dependency_overrides[get_current_user] = lambda: proxy
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth() -> TestClient:
    """TestClient without any auth override - real get_current_user
    applies. Used to verify that unauthenticated requests return 401."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_other_group(other_group_data) -> TestClient:
    with Session(engine) as s:
        user = s.get(User, other_group_data["user_id"])
        proxy = UserProxy(user, [other_group_data["permission_group_id"]])
    app.dependency_overrides[get_current_user] = lambda: proxy
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def cleanup_ingest(base_data):
    yield
    with Session(engine) as session:
        session.exec(
            text("""
                DELETE FROM ingest_external_api_neutron_monitor
                WHERE ingest_id IN (
                    SELECT id FROM ingest
                    WHERE permission_group_id = :pg_id
                )
            """),
            params={"pg_id": base_data["permission_group_id"]},
        )
        session.exec(
            text("""
                DELETE FROM ingest_external_api
                WHERE ingest_id IN (
                    SELECT id FROM ingest
                    WHERE permission_group_id = :pg_id
                )
            """),
            params={"pg_id": base_data["permission_group_id"]},
        )
        session.exec(
            text("DELETE FROM ingest WHERE permission_group_id = :pg_id"),
            params={"pg_id": base_data["permission_group_id"]},
        )
        session.commit()


@pytest.fixture
def cleanup_parser(base_data):
    yield
    with Session(engine) as session:
        # Collect parser IDs belonging to test permission group before deleting
        parser_ids = session.exec(
            text("""
                SELECT parser_id FROM parser_detailed
                WHERE permission_group_id = :pg_id
                AND parser_id != :base_parser_id
            """),
            params={
                "pg_id": base_data["permission_group_id"],
                "base_parser_id": base_data["parser_id"],
            },
        ).all()

        if parser_ids:
            ids = [row[0] for row in parser_ids]

            session.exec(
                text("DELETE FROM parser_csv WHERE parser_id = ANY(:ids)"),
                params={"ids": ids},
            )
            session.exec(
                text("DELETE FROM parser_json WHERE parser_id = ANY(:ids)"),
                params={"ids": ids},
            )
            session.exec(
                text("DELETE FROM parser_mqtt WHERE parser_id = ANY(:ids)"),
                params={"ids": ids},
            )
            session.exec(
                text("DELETE FROM parser_detailed WHERE parser_id = ANY(:ids)"),
                params={"ids": ids},
            )
            session.exec(
                text("DELETE FROM parser WHERE id = ANY(:ids)"),
                params={"ids": ids},
            )

        session.commit()


@pytest.fixture
def cleanup_qc(base_data):
    yield
    with Session(engine) as session:
        session.exec(
            text("""
                DELETE FROM quality_control_function_argument
                WHERE quality_control_function_id IN (
                    SELECT qcf.id FROM quality_control_function qcf
                    JOIN quality_control_setting qcs ON qcs.id = qcf.quality_control_setting_id
                    WHERE qcs.permission_group_id = :pg_id
                )
            """),
            params={"pg_id": base_data["permission_group_id"]},
        )
        session.exec(
            text("""
                DELETE FROM quality_control_function
                WHERE quality_control_setting_id IN (
                    SELECT id FROM quality_control_setting
                    WHERE permission_group_id = :pg_id
                )
            """),
            params={"pg_id": base_data["permission_group_id"]},
        )
        session.exec(
            text(
                "DELETE FROM quality_control_setting WHERE permission_group_id = :pg_id"
            ),
            params={"pg_id": base_data["permission_group_id"]},
        )
        session.commit()
