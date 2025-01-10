import pytest
from docker import DockerClient
from docker.models.containers import ExecResult, Container


@pytest.fixture(scope="session")
def docker() -> DockerClient:
    cl = DockerClient.from_env()
    yield cl
    cl.close()


@pytest.fixture(scope="module")
def container(request, docker: DockerClient) -> Container:
    return docker.containers.get(request.param)


@pytest.fixture(scope="module")
def frontend(docker) -> Container:
    return docker.containers.get("tsm-orchestration-frontend-1")


'python3 manage.py loaddata --format json - < "$DATAFILE"'

#
#def test_create_thing(self, frontend, thing):
#    pass
#    # frontend.exec_run('python3 manage.py loaddata --format json {thing}')
#    # TODO:
#    #   - get GroupID and ProjectID from frontendDB (?)
#    #   - create a Thing
#    #       - either via `python3 manage.py loaddata --format json {thing}`
#    #       - or via a POST to `{base_url}/frontend/tsm/thing/`


