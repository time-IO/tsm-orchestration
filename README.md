# Get started with ZID/TSM

```
docker-compose up -d
```

# Simulate creating a new thing

```
docker-compose run --rm dispatcher-producer --topic thing_created -k kafka:9092 -v produce "{\"uuid\":\"057d8bba-40b3-11ec-a337-125e5a40a845\",\"name\":\"Axel F.\"}"
```

The dispatcher will create a new minio user and bucket: http://localhost:9001/buckets/axelf-057d8bba-40b3-11ec-a337-125e5a40a845/browse


# MinIO: Find the current event ARN to configure bucket notifications

```bash
mc admin info  myminio/ --json | jq .info.sqsARN
```