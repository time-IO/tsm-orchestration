DROP VIEW IF EXISTS "sta_datastream_links" CASCADE;
CREATE VIEW "sta_datastream_links" AS
-- Maps a time.IO thing to its STA datastreams ("DATASTREAMS"."ID" = device property id):
-- the STA views carry no thing uuid, and the grafana user cannot read public.sms_*.
SELECT DISTINCT
    sdl.thing_id            AS t_uuid,
    sdl.device_property_id  AS sta_datastream_id
FROM public.sms_datastream_link sdl
