#!/usr/bin/env bash

rm -rf data/kafka/config data/kafka/data
rm -rf data/zookeeper/data
rm -rf data/minio/vol0/* data/minio/vol0/.minio.sys
rm -rf data/minio/vol1/* data/minio/vol1/.minio.sys
rm -rf data/minio/vol2/* data/minio/vol2/.minio.sys
rm -rf data/minio/vol3/* data/minio/vol3/.minio.sys
rm -rf data/postgres/data