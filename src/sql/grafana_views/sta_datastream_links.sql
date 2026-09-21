DROP VIEW IF EXISTS "sta_datastream_links" CASCADE;
CREATE VIEW "sta_datastream_links" AS
WITH base AS (
    SELECT
        sdl.id            AS link_id,
        sdl.thing_id      AS t_uuid,
        sdl.datastream_id AS ds_id,
        sdl.begin_date,
        sdl.end_date,
        concat_ws(
            ':',
            NULLIF(c.label, ''),
            NULLIF(d.short_name, ''),
            NULLIF(dp.property_name, ''),
            NULLIF(dp.label, '')
        ) AS base_name
    FROM public.sms_datastream_link sdl
    LEFT JOIN public.sms_device_property dp ON dp.id = sdl.device_property_id
    LEFT JOIN public.sms_device_mount_action dma ON dma.id = sdl.device_mount_action_id
    LEFT JOIN public.sms_device d ON d.id = dma.device_id
    LEFT JOIN public.sms_configuration c ON c.id = dma.configuration_id
)
SELECT
    link_id,
    t_uuid,
    ds_id,
    begin_date,
    end_date,
    -- Append the link id when the SMS name is not unique within a thing,
    -- so consecutive settings don't collapse to identical panel titles.
    CASE
        WHEN count(*) OVER (PARTITION BY t_uuid, base_name) > 1
        THEN concat(base_name, ' (#', link_id, ')')
        ELSE base_name
    END AS name
FROM base
