#!/bin/bash
alembic revision --autogenerate
alembic upgrade head
fastapi dev --host 0.0.0.0 --port 8000 main.py
