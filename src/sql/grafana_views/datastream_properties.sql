DROP VIEW IF EXISTS "datastream_properties" CASCADE;
CREATE VIEW "datastream_properties" AS
SELECT
    tsm_ds."position",
    tsm_ds.id  AS "ds_id",
    tsm_t.uuid AS "t_uuid"
FROM datastream tsm_ds
JOIN thing tsm_t ON tsm_ds.thing_id = tsm_t.id
