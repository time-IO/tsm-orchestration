DROP VIEW IF EXISTS "sta_datastream_links" CASCADE;
CREATE VIEW "sta_datastream_links" AS
-- Maps a time.IO thing to the STA datastreams linked to it: the STA views carry
-- no thing uuid, and the grafana user cannot read public.sms_*. The datastream id
-- is "DATASTREAMS"."ID" (= device property id), i.e. all data is read from the
-- STA views, this view only scopes it to one time.IO thing.
SELECT DISTINCT
    sdl.thing_id            AS t_uuid,
    sdl.device_property_id  AS sta_datastream_id
FROM public.sms_datastream_link sdl
