SET search_path TO config_db;

ALTER TABLE "qaqc"
ADD COLUMN "is_active" BOOL NOT NULL default FALSE;

CREATE UNIQUE INDEX "unique_active_qaqc_per_project"
ON "qaqc" (project_id)
WHERE "is_active" = TRUE;
