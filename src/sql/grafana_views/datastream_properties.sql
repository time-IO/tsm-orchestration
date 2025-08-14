DROP VIEW IF EXISTS "datastream_properties" CASCADE;
CREATE VIEW "datastream_properties" AS
SELECT DISTINCT
    case
        when dp.property_name is null or dp.unit_name is null
        then tsm_ds.position
        else concat(dp.property_name, ' - ', dp.label, ' (', dp.unit_name, ')', ' - ', tsm_ds."position"::text)
    end as "property",
    tsm_ds."position",
    tsm_ds.id as "ds_id",
    tsm_t.uuid as "t_uuid"
FROM datastream tsm_ds
JOIN thing tsm_t ON tsm_ds.thing_id = tsm_t.id
LEFT JOIN public.sms_datastream_link sdl ON tsm_t.uuid = sdl.thing_id AND tsm_ds.id = sdl.datastream_id
LEFT JOIN public.sms_device_property dp ON sdl.device_property_id = dp.id
LEFT JOIN public.sms_device_mount_action dma on dma.id = sdl.device_mount_action_id
