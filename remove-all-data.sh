#!/usr/bin/env bash

rm -rf data/minio/vol0/* data/minio/vol0/.minio.sys data/minio/vol0/.writable-check-*
rm -rf data/minio/certs/*
rm -rf data/postgres/data/*
touch data/postgres/data/.gitkeep
rm data/mosquitto/auth/mosquitto.acl
rm data/mosquitto/auth/mosquitto.passwd
rm -rf data/grafana/*