
## prerequisite
- test if external services are up, running and reachable
   - Databases: observationDB, configDB, FE-DB, (SMS-DB), (CV-DB)
   - APIs: CV-API, SMS-API
- test if docker project (tsm-orchestration) is up and running
   - `python-on-whales`

## tests

1. public endpoints reachable
   - ...
2. user login test
    - EXPECT grafana permissions were updated
3. thing creation in existing project
    - EXPECT mqtt message is send
    - EXPECT new thing in database
    - EXPECT new thing in configdb
    - EXPECT new grafana dashboard for thing
4. thing creation in new project
    - (same as in 2.)
    - EXPECT new db schema
5. thing update
    - EXPECT mqtt message is send
    - EXPECT thing in database changed
    - EXPECT thing in configdb changed
    - EXPECT grafana dashboard for thing changed
6. mqtt data ingest success
    - EXPECT data in database
    - EXPECT journal info entry
7. mqtt data ingest fails
    - EXPECT journal error entry
8. file data ingest success
    - EXPECT data in database
    - EXPECT journal info entry
9. file data ingest fails
    - EXPECT journal error entry
10. cron
    - sms sync
    - EXPECT data in database
    - EXPECT journal info entry
    - cv sync
    - api fetch