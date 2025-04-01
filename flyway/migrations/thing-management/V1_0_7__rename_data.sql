BEGIN;

ALTER TABLE ext_api_type
    RENAME TO external_api_type;

ALTER TABLE ext_api_ingest
    RENAME TO external_api_ingest;

ALTER TABLE ext_sftp_ingest
    RENAME TO external_sftp_ingest;

ALTER TABLE "thing"
    RENAME COLUMN "raw_data_storage" TO "enable_raw_data_storage";

ALTER TABLE external_sftp_ingest
    RENAME CONSTRAINT "fk_ext_sftp_thing" TO "fk_external_sftp_thing";

COMMIT;
