# Get started with ZID/TSM

```
docker-compose up -d
```

# Minio

Yes, we really need four volumes, otherwise object lock will not work.

# Cleanup data dirs

Be careful!

```bash
sudo ./remove-all-data.sh
```

# Kafka

Debugging Kafka events:

```bash
docker-compose logs --follow kafkacat
```


# Simulate creating a new thing

```
docker-compose run --rm dispatcher-producer --topic thing_created -k kafka:9092 -v produce "{\"uuid\":\"057d8bba-40b3-11ec-a337-125e5a40a845\",\"name\":\"Axel F.\"}"
```

The dispatcher will create a new minio user and bucket: <http://localhost:9001/buckets/axelf-057d8bba-40b3-11ec-a337-125e5a40a845/browse>

# Another way of producing new thing

```
cat thing-event-msg.json | tr -d '\n' | docker-compose exec -T kafka kafka-console-producer.sh --broker-list kafka:9092 --topic thing_created
```

Be aware of the `tr` step - `kafka-console-producer` is processing all
input line by line and will break multiline (JSON) strings.


# MinIO: Find the current event ARN to configure bucket notifications

```bash
mc admin info  myminio/ --json | jq .info.sqsARN
```

# Naming conventions

Human readable ID for projects and things: Use UUID as suffix and
sanitized name to fill it from the left until it is 63 chars long.

```pathon
import re


def slug(self):
    return re.sub(
        '[^a-z0-9_]+',
        '',
        '{shortname}_{uuid}'.format(shortname=self.name[0:30].lower(), uuid=self.uuid)
    )
    
# Or with minus chars at all but less space for the name
    def slug_with_minus(self):
        return re.sub(
            '[^a-z0-9\-]+',
            '',
            '{shortname}-{uuid}'.format(shortname=self.name[0:26].lower(), uuid=self.uuid)
        )
```
