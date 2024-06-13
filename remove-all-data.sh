#!/usr/bin/env bash

rm -r data/minio/vol0/* data/minio/vol0/.minio.sys
rm -r data/minio/certs/*
rm -r data/postgres/data/*
rm data/mosquitto/auth/mosquitto.acl
rm data/mosquitto/auth/mosquitto.passwd
rm -r data/grafana/*
rm -r data/tomcat/context/*
rm cron/crontab.txt && touch cron/crontab.txt
exit 0
