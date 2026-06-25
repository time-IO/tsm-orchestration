# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
