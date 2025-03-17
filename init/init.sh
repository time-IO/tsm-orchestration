#!/usr/bin/env sh

mkdir -p /tmp/minio/certs
mkdir -p /tmp/minio/vol0

# 1. Always copy SSH key from host if it exists
#    - If not, check if it exists in certs
#    - If not, generate a new SSH key
if [ -f "/tmp/hostcerts/id_ed25519" ]; then
    echo "Copying SSH key from host."
    cp /tmp/hostcerts/id_ed25519 /tmp/minio/certs/id_ed25519
elif [ ! -f "/tmp/minio/certs/id_ed25519" ]; then
    echo "No SSH key found, generating new SSH key."
    ssh-keygen -t ed25519 -f /tmp/minio/certs/id_ed25519 -N ""
fi

# 2. Always copy FTP cert and key from host if they exist
#    - If not, check if they exist in certs and are valid
#    - If not, generate new self-signed certificates
if [ -f "/tmp/hostcerts/minio-ftp.crt" ] && [ -f "/tmp/hostcerts/minio-ftp.key" ]; then
    echo "Copying FTP certificate and key from host."
    cp /tmp/hostcerts/minio-ftp.crt /tmp/minio/certs/minio-ftp.crt
    cp /tmp/hostcerts/minio-ftp.key /tmp/minio/certs/minio-ftp.key
else
    if [ ! -f "/tmp/minio/certs/minio-ftp.crt" ] || [ ! -f "/tmp/minio/certs/minio-ftp.key" ] || \
       ! openssl x509 -checkend 604800 -noout -in /tmp/minio/certs/minio-ftp.crt; then
        echo "No valid certificate found, generating new self-signed certificate."
        openssl req -new -newkey ed25519 -days 90 -nodes -x509 \
            -keyout /tmp/minio/certs/minio-ftp.key \
            -out /tmp/minio/certs/minio-ftp.crt \
            -subj "/C=DE/O=Helmholtz-Zentrum für Umweltforschung GmbH - UFZ/OU=RDM/CN=ZID TSM Development CA" \
            -addext "subjectAltName = DNS:localhost" \
            -addext "basicConstraints=critical,CA:FALSE"
    fi
fi

# Make nginx proxy landing page content accessible for all users

tree -pugfi /home/tsm/html

chmod a+x /home/tsm/html
chmod a+x /home/tsm/html/css
chmod a+x /home/tsm/html/images
chmod -R a+r /home/tsm/html

tree -pugfi /home/tsm/html

# Create crontab.txt if it not already exists
if [ ! -f "/tmp/cron/crontab.txt" ]; then
    touch "/tmp/cron/crontab.txt"
    chmod 666 "/tmp/cron/crontab.txt"
fi

mkdir -p /tmp/mqtt/auth
mkdir -p /tmp/mqtt/data
