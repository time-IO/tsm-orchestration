ALTER TABLE qaqc_setting ADD CONSTRAINT name_uniq UNIQUE ("name");
ALTER TABLE qaqc_setting_function DROP COLUMN "position";
