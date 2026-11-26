#!/bin/bash

set -e

# renders the crontab from the DSM DB and supervises supercronic
exec python3 /scripts/cron_scheduler.py
