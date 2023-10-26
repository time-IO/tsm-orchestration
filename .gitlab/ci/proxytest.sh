#!/bin/bash

PROXY_IP=$(docker inspect tsm-orchestration-proxy-1 | jq -r .[].NetworkSettings.Networks.\"tsm-orchestration_default\".IPAddress)
GATEWAY_IP=$(docker inspect tsm-orchestration-proxy-1 | jq -r .[].NetworkSettings.Networks.\"tsm-orchestration_default\".Gateway)

curl --version

echo "running proxytest.sh"
echo "checking http://${PROXY_IP}:80"
curl ${PROXY_IP}:80 && echo yes || echo no
echo ""
echo "checking http://${PROXY_IP}"
curl ${PROXY_IP} && echo yes || echo no
echo ""
echo "checking http://${GATEWAY_IP}:80"
curl ${GATEWAY_IP}:80 && echo yes || echo no
echo ""
echo "checking http://${GATEWAY_IP}"
curl ${GATEWAY_IP} && echo yes || echo no

