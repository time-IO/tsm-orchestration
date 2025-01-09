

## Run on stage 

We provide a script that runs the test suite. 
```bash
./run_tests.sh
```

```bash
cd /home/tsm-orchestration/tsm-orchestration
source ../tests_venv/bin/activate
PGSSLROOTCERT=/etc/ssl/certs/ca-certificates.crt pytest --dc-env-file=.env tests -v
```

The environment variable `PGSSLROOTCERT` is necessary, because we test some 
database connections from the host system. 
From within containers the certificates might have been set there or are not needed, 
depending on the connection option `sslmode`.


## Run locally (for test suite development)

From within the orchestration directory run
```bash
pytest --env=.env --env=tests/local.env tests -v
```


## Hints / Files
- `requirements_tests.txt`: holds pip dependencies for the tests
- `tests/conftest.py`: adds `-E/--dc-env-file FILE` option to pytest and handles the merging of dotenv-files

