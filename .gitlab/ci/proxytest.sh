#!/bin/bash
PROXY_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' tsm-orchestration-proxy-1)
PROXY_IP2=$(docker inspect tsm-orchestration-proxy-1 | jq -r .[].NetworkSettings.Networks.\"tsm-orchestration_default\".IPAddress)
GATEWAY_IP=$(docker inspect tsm-orchestration-proxy-1 | jq -r .[].NetworkSettings.Networks.\"tsm-orchestration_default\".Gateway)
echo "running proxytest.sh"
echo "checking http://${PROXY_IP}:80"
curl http://${PROXY_IP}:80 && echo yes || echo no
echo "checking http://${PROXY_IP}"
curl http://${PROXY_IP} && echo yes || echo no
echo "checking http://${PROXY_IP2}:80"
curl http://${PROXY_IP2}:80 && echo yes || echo no
echo "checking http://${PROXY_IP2}"
curl http://${PROXY_IP2} && echo yes || echo no
echo "checking http://${GATEWAY_IP}:80"
curl http://${GATEWAY_IP}:80 && echo yes || echo no
echo "checking http://${GATEWAY_IP}"
curl http://${GATEWAY_IP} && echo yes || echo no

