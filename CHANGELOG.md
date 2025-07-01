# Changelog
- Use `Added`, `Changed`, `Fixed`, `Removed`

## [Unreleased]

### Added
- MQTTDeviceType `chirpstack-generic` ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/383))
- option to use header names as datastream names in CsvParser ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/347))

### Changed
- Refactoring python code for Grafana workers ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/375))
- Tsystems API due to changed response ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/398))

### Fixed
- Pass CSV parser warnings to dashboard journal ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/388))

## 2025-06-18

### Added
- Option to use self-hosted docker images ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/386))
- Additional parameters for TTN API ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/387))

### Fixed
- Authentication in TSystems API ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/387))

## 2025-06-12

### Added
- Option to disable the database service ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/358))
- Option to sort and filter columns in Grafana dashoard journal ([Merge Request1](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/366), [Merge Request 2](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/364), [Merge Request 3](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/362), [Merge Request 4](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/360))
- Component tests

### Changed
- Migrated `observation` tables from timescaleDB Hypertables to 'normal' Postgres tables ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/379))
- Added ID Column to `observation` tables ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/348))
- New worker for cron scheduled jobs ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/351))
- Handle failing external API calls gracefully ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/377))

### Fixed
- Duplicated configDB entries ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/287))
- Incompatable timeouts for FROST froze STA requests ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/371))

## 2025-03-28

### Fixed
- Bug when running the QC-Settings ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/343))

## 2025-03-27

### Fixed
- Bug when saving the QC-Settings ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/341))

## 2025-03-26

### Changed
- Switching to materialized views for SMS data ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/326))

### Fixed
- Idle State when creating views for frost ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/336))
- Bug, when Saving a QaQc Test ([Merge Request](https://codebase.helmholtz.cloud/ufz-tsm/tsm-orchestration/-/merge_requests/337))

## 2025-03-19
