#!/bin/bash
PROXY_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' tsm-orchestration-proxy-1)
echo $PROXY_IP
echo "checking http://${POXY_IP}:80"
curl -I http://$PROXY_IP:80 && echo yes || echo no
echo "checking http://${POXY_IP}"
curl -I http://$PROXY_IP && echo yes || echo no
echo "checking http://localhost"
curl -I http://localhost && echo yes || echo no
echo "checking http://127.0.0.1"
curl -I http://127.0.0.1 && echo yes || echo no
echo "checking http://docker"
curl -I http://docker && echo yes || echo no
cho "checking http://docker."
curl -I http://docker. && echo yes || echo no
echo "checking http://docker:80"
curl -I http://docker:80 && echo yes || echo no
cho "checking http://docker.:80"
curl -I http://docker.:80 && echo yes || echo no
echo "checking http://proxy"
curl -I http://proxy && echo yes || echo no
echo "checking http://proxy."
curl -I http://proxy. && echo yes || echo no
echo "checking http://proxy:80"
curl -I http://proxy:80 && echo yes || echo no
echo "checking http://proxy.:80"
curl -I http://proxy.:80 && echo yes || echo no
