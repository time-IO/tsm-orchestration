

## Run on stage 

```bash
cd /home/tsm-orchestration/tsm-orchestration
source ../tests_venv/bin/activate
pytest --env=.env tests -v
```


## Run locally (for test suite development)

From within the orchestration directory run
```bash
pytest --env=.env --env=tests/local.env tests -v
```


## Hints / Files
- `requirements_tests.txt`: holds pip dependencies for the tests
- `tests/conftest.py`: adds `--env FILE` option to pytest and handles the merging of dotenv-files

