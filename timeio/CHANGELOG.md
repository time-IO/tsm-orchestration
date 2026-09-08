# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.2] - 2026-09-08

- Added `object-storage.persistence.size` so deployments can size the
  S3-compatible data PVC independently; the generic default remains `100M`.

## [0.6.1] - 2026-08-28

- Replaced the default object-storage runtime with pinned
  `docker.io/pgsty/silo:RELEASE.2026-08-06T00-00-00Z@sha256:29a498b24669cae1fed11c1a2fb2b3d73c68829a0a9c0b14e71b386671d38fac`
  and switched the server executable to `silo` while preserving the
  MinIO-compatible S3, Console, MQTT, FTP/FTPS, SFTP, and data-path settings.
- Added disabled-by-default MinIO FTP/SFTP chart values for protocol command
  flags, Service ports, passive FTP ports, and cert/key Secret mounts.

## [0.5.2] - 2026-08-11

- Fixed the generated `worker-file-ingest` `DSMDB_DSN` Secret value to use the
  DSM database credentials and a valid PostgreSQL port.

## [0.5.1] - 2026-07-06

- Removed the unused object-storage certificate Secret and `/certs` mount from
  the Helm deployment. If FTP/SFTP support is needed in Helm later, reintroduce
  it as a values-gated feature with MinIO flags, service ports, and cert/key
  Secret together. See #3.

## [0.4.3] - 2026-06-25

- Use a `Recreate` rollout strategy for object-storage so updates do not try to
  mount its ReadWriteOnce data volume from two pods at the same time.

## [0.4.2] - 2026-06-25

- Marked the Flyway Job as an Argo CD sync hook so completed migration Jobs do
  not remain continuously desired resources after Kubernetes TTL cleanup.

## [0.1.8] - unreleased

- added `prod-<YYYY-mm-DD>` image tags for workers, cron-scheduler, frost service

## [0.1.7] - 2025-04-02

- changed database service to use bitnami postgresql helm chart
- fixed mqtt topics used by services
- updated image tags

## [0.1.1] - [0.1.6]

- changes not documented

## [0.1.0] - 2025-02-12
- initial release
- previous alpha releases are not documented
