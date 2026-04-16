-- First, insert the database record
INSERT INTO config_db.database (
    id,
    schema,
    "user",
    password,
    ro_user,
    ro_password,
    url,
    ro_url
) VALUES (
    1,
    'test-schema',
    'database-user',
    'database-password',
    'test',
    'test',
    'testdb',
    'ro_url'
);

-- Then insert the project
INSERT INTO config_db.project (
    id,
    name,
    uuid,
    database_id
) VALUES (
      1,
      'bento-test-project',
      '0de9a608-da28-48da-991c-3eb00b24f30c',
      1
     );

-- Then insert the thing
INSERT INTO config_db.thing (
    id,
    uuid,
    name,
    project_id,
    ingest_type_id,
    mqtt_id,
    ext_mqtt_id
) VALUES (
    1,
    'b170ddaa-1a2c-4243-9209-5d49a8d7f335',
    'bento-test-thing',
    1,
    5,
    1,
    1
);

-- Then insert the mqtt
INSERT INTO config_db.mqtt (
    id,
    "user",
    password,
    password_hashed,
    topic,
    mqtt_device_type_id
) VALUES (
    1,  -- id
    'test-bento-user',
    'eqvu8wX6fgnTHmIfXKxlRXvI9wpU1I9QnCL7HonL',
    'PBKDF2$sha512$600000$RUR3cGRWZ3diTWNvZEhEUTlqaW5sTQ==$4frK8+vW8mmVT48j0vsef812jnh8m9YTDaozMzIopfl57Pxl4T5IHnHlJQoI0XyVnLd7q0poS4sYTfli+zn9jw==',
    'bento-test-topic',
    1
);

-- Finally, insert the ext_mqtt
INSERT INTO config_db.ext_mqtt (
    id,
    external_mqtt_address,
    external_mqtt_port,
    external_mqtt_username,
    external_mqtt_password,
    external_mqtt_ca_cert,
    external_mqtt_client_cert,
    external_mqtt_client_key,
    external_mqtt_topic
) VALUES (
    1,
    'chirpstack.web-intern-stage.app.ufz.de',
    8883,
    '',
    '',
    '-----BEGIN CERTIFICATE-----MIIFCTCCAvGgAwIBAgIUQRxGfesit7xM+eU+41hS/BX4MuMwDQYJKoZIhvcNAQENBQAwHDEaMBgGA1UEAxMRQ2hpcnBzdGFjay1VRlogQ0EwHhcNMjUwNTE2MTIxNzAwWhcNMzAwNTE1MTIxNzAwWjAcMRowGAYDVQQDExFDaGlycHN0YWNrLVVGWiBDQTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBALlcWUm+cCnD36lVaESHeyK3snW3Yqh2Bvksi88QQded5Pv7wk0gRGAhNFDnhotqF1SjBD4olUG5Mt8rHc1KcpWyaERcQtiR/s+JSfm1j/tCwX/w4TPzhOqFJ5OUal7ZR0lbsLFLs7Rtf+0h4qEJKxTo4tE/jaOS8BNE4sCV/Rxy62V3Gux2SojOds6DhCbBpA9dThg6GCOCFs3sqWbcCPgd/fuoNRB2v2zDT875FpF8xpgk4fYuPkY9APLCjx6MIe6S/8Mrlc2kUzyOZTDhCPSXpPC4cVrtS3ooxzwFKPpmGqYhnY1266r7LV652VeGQ+i1W51KxuD4CIN+KRNmlsdbbI7emX4dOz1VymVSqAqgazQJc4MVh3Y9IO3tWz+9q5jZgv4FaWSEERXtOzz1QNZDp3w/fLtV8RNNu/Bo/ZkfgKmDecmXpHaEriuYgjADEha8lBlBmOXCsivHblT5o954yyWKg9GAvM54l77FaBjLGVxu1UlzuVfe5WuJ9FZ23kxRNSi6VoR7IX6e4XbLOfohtqqCUZRaYDq5SblxnonBMkm9P/8yfVFhyPQc4I8eJlc40YtdiX9cmAPKcOsPDSGKfNh+7s8NZ4w+KftXLk6bQPaMtiQ2Zy1kxq7HSYmwWEGnAs08RxbTxSZoZO8Uhc33ESYTGx/hB1gtSXwP7i85AgMBAAGjQzBBMA8GA1UdDwEB/wQFAwMHBgAwHQYDVR0OBBYEFLwZLAzwGvEbDfb5YGy0d7+iMq9wMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQENBQADggIBAFksisHuMpP4s1hc7jX946H0mUaXiZ+9pBALVf+jm7I8Ak9rb/1qngqEnw4CJhFYlVzjt/oF+wBVr+w9wNjrEv7LHPqDQEEMbVvqTHQzc1d8tNPgDzOO3nXAxVKc4CivDGUsXh8B++Bd6L0xUL3UIakQIkFR17cwQ8PjISqAS8+e5VsIxOPvL/j52yLfQc2Qv4WLK9O8z8DdC665WuPpUB4A6+3JLeYV7OWWFofd6diKlngAbhdqYJxDCAxEti2lLB6tEKOvIycwIZlWkTvG0L0nlURcHy+Cww736yDQrJlGm4nR3UwTl9tEY6O+/ekxpZ1KEonex8gOOAFnS9ZmuoIhDtKV0x9blOhzQe1kbKh3NUz6v/eRggOROYJga7FKaSi00Gt/i/YH1aVVS95gWkoWwr9EVKmhP+QsXmLC4PyxfpxRjDty65Z71T0izdgzEBbcd5H4AUkQGLMOPrxshSbwhhRpPgWsZSCOuUGJyk6lj2FeSttZsJd1NKzms9Zys79YC7ReElux+D4PcVDqvLYSNLA0u2FilIf794I/aDh3p1GoGa8maSpijkhGvgoROgCMzJYUi1u9IDvmIi2R2FqP1uPACQUTTx/ayYw0I6AzCG2xnJ4TWKCThkz88eAScbK6HPqazpzVATEgZcC1OPCbQaCHW1TPkzYSdciYXuPs-----END CERTIFICATE-----',
    '-----BEGIN CERTIFICATE-----MIIDiDCCAXCgAwIBAgIUFU9V0MpUsnoExQW/rRfT4OIgPKUwDQYJKoZIhvcNAQENBQAwHDEaMBgGA1UEAxMRQ2hpcnBzdGFjay1VRlogQ0EwHhcNMjUxMDAyMTMyNDIzWhcNMzAxMDAyMjMwMDIzWjAvMS0wKwYDVQQDDCRlMjA4ZjAzNi03YmY4LTQxYzctYTRlNS0zZDBmNjc2ZTMwNjAwWTATBgcqhkjOPQIBBggqhkjOPQMBBwNCAATEqAQoMl3UYviyTjUs6QEEiDFUluRDaGWdcpWhR7tsVYzKIgWE5DdI3R71CuwW4zAcUFwGsJVL5UKMzsNu3afso3oweDAfBgNVHSMEGDAWgBS8GSwM8BrxGw32+WBstHe/ojKvcDAvBgNVHREEKDAmgiRlMjA4ZjAzNi03YmY4LTQxYzctYTRlNS0zZDBmNjc2ZTMwNjAwDwYDVR0PAQH/BAUDAweAADATBgNVHSUEDDAKBggrBgEFBQcDAjANBgkqhkiG9w0BAQ0FAAOCAgEASIamMBy/3LNJ8UsPBb0XV5JOezqeBUlRzXlQFJSYBU9va6AydMXXN8Jb14JOJtdN/zj3gfQXdzhyyf7t40mipE73B4S5NPx88jOmLMON+gkS3z3poW0rE7ZF/9JXM8OJwmwXgSH2bQp69cjVIEdTlWWYOJHIXRVaef7k+mgPUYcDjTapAl8GHUy1kT8VFjPGynN1a3RwlYYcqnylxTQcDQKLEaaaTWs3iQrLDMbjlD+7zHYhJn5vRJZCgF0oBIdPYVtkNmv9icmjY/13vvJSkErx+4W6sbQwrH3S27NBMSa+yJapMKXgzqcczzhjnZPnIc9QDf3rmAVyiqUZ72vvjTZWAvITIwmaRW5QZYltoVNwY9oLhNyPx7WtVdhjJLESVT+23P+wjw5eRwZokde46jt79NMeBpczn4maq/YIzRIJBtP5pLg4NA6j9UfDH7GKobdQ095wDJg6hbdMV3mSE6kK+uSAvryRfHir3kU5jHcMFeCKDYWKn6qaA2M8K/27nbeGT7HxkQODF3byK7C9zLGGepnbTCvMHjTm84qtFGagAWPx5+Mz4ZL9UFZo6u6/9wOMTii2XF/hM+MhD5R+q+NaCMB9oDk6sV1DW0lyPW/WgGnmNdmaVlZbm2JhQkyUOaNgHoCx8COEhOB+LDrfkHJwdOKIKRakY2nr0p6TesU=-----END CERTIFICATE-----',
    '-----BEGIN PRIVATE KEY-----MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgZ4AZl4MHuxdWvACuuyIEpl0SonCAUhSh13sq+DxtByihRANCAATEqAQoMl3UYviyTjUs6QEEiDFUluRDaGWdcpWhR7tsVYzKIgWE5DdI3R71CuwW4zAcUFwGsJVL5UKMzsNu3afs-----END PRIVATE KEY-----',
    '#'
);