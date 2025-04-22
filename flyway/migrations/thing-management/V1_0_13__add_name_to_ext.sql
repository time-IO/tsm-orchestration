-- Migration: Add 'name' column to external_sftp_ingest and external_api_ingest

BEGIN;

ALTER TABLE external_sftp_ingest
    ADD COLUMN "name" VARCHAR(200) NOT NULL DEFAULT 'Unnamed SFTP Ingest';

ALTER TABLE external_api_ingest
    ADD COLUMN "name" VARCHAR(200) NOT NULL DEFAULT 'Unnamed API Ingest';

COMMIT;
