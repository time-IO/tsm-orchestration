#!/usr/bin/env bash

rm -rf data/minio/vol0/* data/minio/vol0/.minio.sys data/minio/vol0/.writable-check-*
rm -rf data/minio/vol1/* data/minio/vol1/.minio.sys data/minio/vol1/.writable-check-*
rm -rf data/minio/vol2/* data/minio/vol2/.minio.sys data/minio/vol2/.writable-check-*
rm -rf data/minio/vol3/* data/minio/vol3/.minio.sys data/minio/vol3/.writable-check-*
rm -rf data/postgres/data/*
touch data/postgres/data/.gitkeep
rm data/mosquitto/auth/mosquitto.acl
rm data/mosquitto/auth/mosquitto.passwd
rm -rf data/grafana/*