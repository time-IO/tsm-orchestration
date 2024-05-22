#!/usr/bin/env sh

# Create a SSH private key file when it is not already present for object storage (minio) sftp service
ls -lah /tmp/minio/certs/id_ed25519 2>/dev/null || ssh-keygen -t ed25519 -f /tmp/minio/certs/id_ed25519 -N ""

# Create TLS key and cert for object storage (minio) FTP service when not already present or expired
ls -lah /tmp/minio/certs/minio-ftp.key /tmp/minio/certs/minio-ftp.crt 2>/dev/null \
  && openssl x509 -enddate -noout -in /tmp/minio/certs/minio-ftp.crt -checkend 604800 \
  || openssl req -new -newkey ed25519 -days 90 -nodes -x509 \
    -keyout /tmp/minio/certs/minio-ftp.key \
    -out /tmp/minio/certs/minio-ftp.crt \
    -subj "/C=DE/O=Helmholtz-Zentrum für Umweltforschung GmbH - UFZ/OU=RDM/CN=ZID TSM Development CA" \
    -addext "subjectAltName = DNS:localhost" \
    -addext "basicConstraints=critical,CA:FALSE"

# Create crontab.txt if it not already exists
if [ ! -f "/tmp/cron/crontab.txt" ]; then
    touch "/tmp/cron/crontab.txt"
    chmod 666 "/tmp/cron/crontab.txt"
fi
tree -pugfi /tmp/cron

tree -pugfi /tmp
