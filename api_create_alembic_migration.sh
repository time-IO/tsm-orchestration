#!/bin/bash
docker compose run --entrypoint "alembic revision --autogenerate -m '$1'" api
