#!/usr/bin/env sh

#############
# variables #
#############

MINIO_CERT_SOURCE="/tmp/bind/minio"
MINIO_CERT_TARGET="/tmp/volume/minio/certs"
MQTT_CERT_SOURCE="/tmp/bind/mqtt"
MQTT_CERT_TARGET="/tmp/volume/mqtt/certs"
CRONTAB="/tmp/volume/cron/crontab.txt"


##################################
#  create volume subdirectories  #
##################################

mkdir -p $MINIO_CERT_TARGET
mkdir -p /tmp/volume/minio/vol0
mkdir -p $MQTT_CERT_TARGET
mkdir -p /tmp/volume/mqtt/auth
mkdir -p /tmp/volume/mqtt/data
mkdir -p /tmp/volume/cron
mkdir -p /tmp/volume/database/pgdata

####################
#  object-storage  #
####################

# 1. Always copy SSH key from host if it exists
#    - If not, check if it exists in volume
#    - If not, generate a new SSH key
echo "Preparing SSH key for MinIO."
if [ -f "${MINIO_CERT_SOURCE}/id_ed25519" ]; then
    echo "Copying SSH key from host."
    cp ${MINIO_CERT_SOURCE}/id_ed25519 ${MINIO_CERT_TARGET}/id_ed25519
elif [ ! -f "${MINIO_CERT_TARGET}/id_ed25519" ]; then
    echo "No SSH key found in MinIO persistence volume, generating new SSH key."
    ssh-keygen -t ed25519 -f ${MINIO_CERT_TARGET}/id_ed25519 -N ""
else
    echo "SSH key already present in MinIO persistence volume."
fi

# 2. Always copy FTP cert and key from host if they exist
#    - If not, check if they exist in volume and are valid
#    - If not, generate new self-signed certificates
echo "Preparing FTP certificate and key for MinIO."
if [ -f "${MINIO_CERT_SOURCE}/minio-ftp.crt" ] && [ -f "${MINIO_CERT_SOURCE}/minio-ftp.key" ]; then
    echo "Copying FTP certificate and key from host to MinIO persistence volume."
    cp ${MINIO_CERT_SOURCE}/minio-ftp.crt ${MINIO_CERT_TARGET}/minio-ftp.crt
    cp ${MINIO_CERT_SOURCE}/minio-ftp.key ${MINIO_CERT_TARGET}/minio-ftp.key
else
    if [ ! -f "${MINIO_CERT_TARGET}/minio-ftp.crt" ] || [ ! -f "${MINIO_CERT_TARGET}/minio-ftp.key" ] || \
       ! openssl x509 -checkend 604800 -noout -in ${MINIO_CERT_TARGET}/minio-ftp.crt; then
        echo "No valid certificate found in MinIO persistence volume, generating new self-signed certificate."
        openssl req -new -newkey rsa:2048 -days 90 -nodes -x509 \
            -keyout ${MINIO_CERT_TARGET}/minio-ftp.key \
            -out ${MINIO_CERT_TARGET}/minio-ftp.crt \
            -subj "/C=DE/O=Helmholtz-Zentrum für Umweltforschung GmbH - UFZ/OU=RDM/CN=ZID TSM Development CA" \
            -addext "subjectAltName = DNS:localhost" \
            -addext "basicConstraints=critical,CA:FALSE"
        echo "New self-signed certificate and key generated in MinIO persistence volume."
    fi
fi

#################
#  mqtt-broker  #
#################

# 1. Always copy ca.crt, server.cert and server.key from host if they exist
#    - If not, check if cert exist in volume and are valid
#    - If not, generate new self-signed certificates
echo "Preparing TLS certificate and key for Mosquitto."
if [ -f "${MQTT_CERT_SOURCE}/server.crt" ] && \
   [ -f "${MQTT_CERT_SOURCE}/server.key" ] && \
   [ -f "${MQTT_CERT_SOURCE}/ca.crt" ]; then
    echo "Copying ca.crt, server.crt and server.key from host to MQTT persistence volume."
    cp ${MQTT_CERT_SOURCE}/server.crt ${MQTT_CERT_TARGET}/server.crt
    cp ${MQTT_CERT_SOURCE}/server.key ${MQTT_CERT_TARGET}/server.key
    cp ${MQTT_CERT_SOURCE}/ca.crt ${MQTT_CERT_TARGET}/ca.crt
else
    if [ ! -f "${MQTT_CERT_TARGET}/server.crt" ] || \
       [ ! -f "${MQTT_CERT_TARGET}/server.key" ] || \
       [ ! -f "${MQTT_CERT_TARGET}/ca.crt" ] || \
       ! openssl x509 -checkend 604800 -noout -in ${MQTT_CERT_TARGET}/server.crt; then
        echo "No valid certificates found in MQTT persistence volume."
        echo "Generating new self-signed ca.crt ..."
        openssl req -new -newkey rsa:2048 -days 90 -nodes -x509 \
            -keyout ${MQTT_CERT_TARGET}/ca.key \
            -out ${MQTT_CERT_TARGET}/ca.crt \
            -subj "/C=DE/O=Helmholtz-Zentrum für Umweltforschung GmbH - UFZ/OU=RDM/CN=time.IO Development CA" \
            -addext "basicConstraints=critical,CA:TRUE"
        echo "Generate server.key and server.csr ..."
        openssl req -new -newkey rsa:2048 -nodes \
            -keyout ${MQTT_CERT_TARGET}/server.key \
            -out ${MQTT_CERT_TARGET}/server.csr \
            -subj "/C=DE/O=Helmholtz-Zentrum für Umweltforschung GmbH - UFZ/OU=RDM/CN=time.IO Development CA" \
            -addext "subjectAltName = DNS:localhost" \
            -addext "basicConstraints=critical,CA:FALSE"
        echo "Sign server.csr with CA to get server.crt ..."
        openssl x509 -req -days 90 -in ${MQTT_CERT_TARGET}/server.csr \
            -CA ${MQTT_CERT_TARGET}/ca.crt -CAkey ${MQTT_CERT_TARGET}/ca.key -CAcreateserial \
            -out ${MQTT_CERT_TARGET}/server.crt
        echo "New self-signed certificates generated in MQTT persistence volume."
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
if [ ! -f $CRONTAB ]; then
    touch $CRONTAB
    chmod 666 $CRONTAB
    echo "# * * * * * /place-sms-and-other-manual-commands-here.sh" >> $CRONTAB
fi

###########################################
#  set volume ownerships and permissions  #
###########################################

chown -R ${SYSTEM_USER}:${SYSTEM_USER} \
      /tmp/volume/minio \
      /tmp/volume/mqtt \
      /tmp/volume/cron \
      /tmp/volume/database


chmod -R u+rwX,g+rwX \
      /tmp/volume/minio \
      /tmp/volume/mqtt \
      /tmp/volume/cron \
      /tmp/volume/database

