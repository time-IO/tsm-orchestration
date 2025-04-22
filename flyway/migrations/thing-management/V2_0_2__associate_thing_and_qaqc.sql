ALTER TABLE "qaqc_setting"
    ADD COLUMN "thing_id" BIGINT;

ALTER TABLE "qaqc_setting"
    ADD CONSTRAINT "fk_qaqc_setting_thing"
        FOREIGN KEY ("thing_id") REFERENCES "thing" ("id") ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;