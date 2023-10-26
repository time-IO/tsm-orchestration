#!/bin/bash

PROXY_IP=$(docker inspect tsm-orchestration-proxy-1 | jq -r .[].NetworkSettings.Networks.\"tsm-orchestration_default\".IPAddress)
GATEWAY_IP=$(docker inspect tsm-orchestration-proxy-1 | jq -r .[].NetworkSettings.Networks.\"tsm-orchestration_default\".Gateway)

curl --version

echo "running proxytest.sh"
curl http://localhost && echo yes || echo no
curl http://localhost:80 && echo yes || echo no
curl http://127.0.0.1 && echo yes || echo no
curl http://127.0.0.1:80 && echo yes || echo no
curl $PROXY_IP && echo yes || echo no
curl $GATEWAY_IP && echo yes || echo no
