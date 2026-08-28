# TimeIO Silo Object Storage Handoff

Date: 2026-08-28
Agent: silochart
Ticket: OpenProject #21924
Umbrella: OpenProject #13203
Ops: TIO-150

## Status

Done. The TimeIO object-storage chart now defaults to PGSTY Silo instead of
the archived `minio/minio` runtime, and the change was proven with local
Helm renders and disposable Docker runtime tests. No live Kubernetes, Argo CD,
firewall, DNS, or secret material was mutated.

## Merge Requests

- Helm chart MR: https://codebase.helmholtz.cloud/ufz-tsm/helm-deployment/-/merge_requests/57
- UFZ wrapper MR: https://codebase.helmholtz.cloud/ufz-tsm/ufz-deployment/-/merge_requests/10

Open MRs checked before implementation:

- `helm-deployment!56` is open for release `0.6.0`. It does not touch
  `timeio/charts/object-storage`; this change intentionally uses `timeio`
  `0.6.1` as the follow-up chart version.
- `ufz-deployment!9` is open for immutable TimeIO `0.5.2` verification. The
  wrapper MR should be reconciled with that strategy after `timeio` `0.6.1`
  is published.

## Implementation Summary

Changed in `helm-deployment`:

- `timeio/charts/object-storage/values.yaml`
  - default image: `docker.io/pgsty/silo`
  - default tag: `RELEASE.2026-08-06T00-00-00Z`
  - default digest:
    `sha256:29a498b24669cae1fed11c1a2fb2b3d73c68829a0a9c0b14e71b386671d38fac`
  - default executable: `silo`
- `timeio/charts/object-storage/templates/deployment.yaml`
  - renders image as `repository:tag@digest` when `image.digest` is set
  - runs the configured executable, defaulting to `silo`
  - preserves `server --console-address :9001 --json /vol0`
  - preserves FTP/FTPS/SFTP flags, passive port range, Secret refs, and
    `/minio/certs` mount
- Chart metadata:
  - `timeio` version `0.6.1`
  - `object-storage` version `0.0.2`

Changed in `ufz-deployment`:

- `ufz/web-intern-stage/Chart.yaml`
  - wrapper version `0.6.1`
  - `timeio` dependency `0.6.1`
- `ufz/web-intern-test/Chart.yaml`
  - wrapper version `0.6.1`
  - `timeio` dependency `0.6.1`

No wrapper values, Argo Applications, SealedSecrets, or live resources were
changed.

## Silo Image Verification

Primary sources checked on 2026-08-28:

- GitHub latest release:
  https://github.com/pgsty/silo/releases/tag/RELEASE.2026-08-06T00-00-00Z
- Silo repository and compatibility notes:
  https://github.com/pgsty/silo
  https://silo.pgsty.com/compatibility/server/
- Docker image:
  `docker.io/pgsty/silo:RELEASE.2026-08-06T00-00-00Z`

Commands/evidence:

- `curl -fsSL https://api.github.com/repos/pgsty/silo/releases/latest`
  returned tag `RELEASE.2026-08-06T00-00-00Z`, published
  `2026-08-06T14:39:20Z`.
- `skopeo inspect docker://docker.io/pgsty/silo:RELEASE.2026-08-06T00-00-00Z`
  returned manifest index digest
  `sha256:29a498b24669cae1fed11c1a2fb2b3d73c68829a0a9c0b14e71b386671d38fac`.
- The manifest includes linux/amd64 platform digest
  `sha256:da1284931914c3de5fc8e8ad0c43b88e4eb930d20064b36867daba4dfd546a00`
  and linux/arm64 platform digest
  `sha256:2c00469c7b3b9537115727c059873869ec6d82b15fcabf8c75ff9961ae89161f`.

Selected chart image:

`docker.io/pgsty/silo:RELEASE.2026-08-06T00-00-00Z@sha256:29a498b24669cae1fed11c1a2fb2b3d73c68829a0a9c0b14e71b386671d38fac`

## Helm Validation

In `helm-deployment`:

- `git fetch --all --prune`: passed
- `git status --short --branch`: clean before edits, scoped changes after
- `glab mr list --per-page 20 -F json`: confirmed open `!56`
- `helm dependency build timeio`: passed
- `helm lint timeio`: passed
- `helm template timeio timeio >/tmp/timeio-silo-default.yaml`: passed
- Protocol render passed:
  `helm template timeio timeio --set object-storage.ftp.enabled=true --set object-storage.ftp.passivePortRange.enabled=true --set object-storage.ftp.tls.enabled=true --set object-storage.ftp.tls.existingSecret=object-storage-ftp-tls --set object-storage.sftp.enabled=true --set object-storage.sftp.sshPrivateKey.existingSecret=object-storage-sftp-key >/tmp/timeio-silo-protocols.yaml`
- Render grep confirmed pinned Silo image, `silo` executable, `MINIO_*`
  settings, ports `9000`, `9001`, `40021`, `40022`, passive range
  `30000-30010`, `/minio/certs`, `object-storage-ftp-tls`, and
  `object-storage-sftp-key`.
- `helm package timeio --destination /tmp/timeio-silo-chart-package`: produced
  `/tmp/timeio-silo-chart-package/timeio-0.6.1.tgz`.
- `helm template timeio /tmp/timeio-silo-chart-package/timeio-0.6.1.tgz`: passed.
- `git diff --check`: passed.

In `ufz-deployment`:

- `git fetch --all --prune`: passed
- `git status --short --branch`: clean before edits, scoped changes after
- `glab mr list --per-page 20 -F json`: confirmed open `!9`
- Since `timeio` `0.6.1` is not published yet, wrapper validation used the
  locally packaged chart copied into ignored wrapper `charts/` directories.
- `ruby tools/validate-secret-keyrefs.rb`: passed, 137 secret refs checked per
  wrapper, all backed by committed SealedSecrets.
- `helm lint ufz/web-intern-stage`: passed
- `helm lint ufz/web-intern-test`: passed
- `helm template web-intern-stage ufz/web-intern-stage --namespace custom-rdm-timeio`: passed
- `helm template web-intern-test ufz/web-intern-test --namespace custom-rdm-timeio`: passed
- Render grep confirmed pinned Silo image, `silo` executable, FTP/FTPS/SFTP
  flags, passive ports, `/minio/certs`, and existing protocol Secret refs.
- `git diff --check`: passed.

## Disposable Runtime Proof

Default Silo proof:

- Started `docker.io/pgsty/silo:RELEASE.2026-08-06T00-00-00Z@sha256:29a498b24669cae1fed11c1a2fb2b3d73c68829a0a9c0b14e71b386671d38fac`
  with chart-rendered command:
  `silo server --console-address :9001 --json /vol0`.
- Ran as UID/GID `1000:1000`, with all capabilities dropped and
  `no-new-privileges`.
- Used chart-compatible env names:
  `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_SERVER_URL`,
  `MINIO_BROWSER_REDIRECT_URL`, and `MINIO_NOTIFY_MQTT_*`.
- `silo healthcheck ready`: passed.
- AWS CLI S3 `create-bucket`, `put-object`, and `get-object`: passed.
- MQTT notification configured through bundled `mcli`; disposable Mosquitto
  received an `s3:ObjectCreated:Put` event on `object_storage_notification`.

Protocol proofs:

- Started Silo with rendered FTPS/SFTP command flags:
  `--ftp address=:40021`,
  `--ftp passive-port-range=30000-30010`,
  `--ftp tls-private-key=/minio/certs/minio-ftp.key`,
  `--ftp tls-public-cert=/minio/certs/minio-ftp.crt`,
  `--sftp address=:40022`,
  `--sftp ssh-private-key=/minio/certs/id_ed25519`.
- Generated throwaway TLS cert/key and SSH host key under `/tmp`; none were
  committed.
- Silo logged `SFTP Server listening on :40022`.
- Silo logged `Silo FTP(Secure) Server listening on :40021`.
- FTPS PUT/GET with curl: passed.
- SFTP PUT/GET with curl: passed.
- Started separate Silo container with FTP enabled and TLS flags omitted.
- Plain FTP PUT/GET with curl: passed.

Observed nuance:

- When FTPS certificate flags are enabled, plaintext FTP fails with
  `tls: first record does not look like a TLS handshake`. This matches the
  chart switch: plaintext FTP is proven with `ftp.tls.enabled=false`, and FTPS
  is proven with `ftp.tls.enabled=true`.

## Rollout And Rollback Notes

- Merge sequencing: `helm-deployment!56` should either merge first, then this
  branch rebases while keeping `0.6.1`, or reviewers must resolve the
  `timeio/Chart.yaml` version/changelog interaction before publication.
- The UFZ wrapper MR depends on publication of `timeio` `0.6.1`; do not merge
  it into a live rollout path until the chart package exists.
- Rollback is values-level:
  set object-storage image back to the previous MinIO image and set
  `object-storage.command.executable=minio`, then roll the workload normally.
- No live PVC migration was performed. Before live rollout, take a snapshot or
  prove on a copied PVC/data set, then keep the MinIO rollback image available.

## Residual Risks

- Disposable tests prove the chart-rendered runtime contract, not live bucket
  contents or production PVC migration.
- No live Argo/Kubernetes/firewall/DNS state was inspected or mutated.
- Silo is an independent AGPL-3.0-or-later community fork; deployment owners
  should accept the license and maintenance model before rollout.
- External reachability of FTP/FTPS/SFTP through any cluster ingress, firewall,
  HAProxy, or DNS layer remains out of scope and must be validated separately.
