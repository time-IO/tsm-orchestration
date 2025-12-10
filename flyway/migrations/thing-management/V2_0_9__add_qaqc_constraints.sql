ALTER TABLE qaqc_setting ADD CONSTRAINT name_proj_uniq UNIQUE ("name", project_id);
ALTER TABLE qaqc_setting_function DROP COLUMN "position";
