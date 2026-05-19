SELECT_PROJECT_AND_DB = """
    SELECT p."name"     AS "project_name",
        p.uuid          AS "project_uuid",
        p.database_id   AS "project_database_id",
        db."user",
        db."password",
        db.ro_user,
        db.ro_password,
        db."url"
    FROM config_db.project p
    JOIN config_db.database db ON p.database_id = db.id
"""

INSERT_PROJECT = """
    INSERT INTO public.permission_group ("name", uuid, entitlement)
    VALUES (%(project_name)s, %(project_uuid)s, %(project_name)s)
    RETURNING id
"""

INSERT_DB = """
    INSERT INTO public.database (permission_group_id, "username", "password", read_only_username, read_only_password, "url")
    VALUES (%(project_id)s, %(user)s, %(password)s, %(ro_user)s, %(ro_password)s, %(url)s)
"""

GET_PARSER = """
    SELECT fp.file_parser_type_id,
        fp."name",
        fp.params,
        fp."uuid"  as "parser_uuid",
        t.uuid   as "thing_uuid",
        p."uuid" as "project_uuid"
    FROM config_db.file_parser fp
        JOIN config_db.s3_store s3 on s3.file_parser_id = fp.id
        JOIN config_db.thing t on t.s3_store_id = s3.id
        JOIN config_db.project p on p.id = t.project_id \
"""

INSERT_PARSER = """
    INSERT INTO public.parser (uuid, parser_type) VALUES (%(parser_uuid)s, 'csv')
    ON CONFLICT (uuid) 
    DO UPDATE SET
        parser_type = EXCLUDED.parser_type
    RETURNING id
"""
INSERT_PARSER_DETAILED = """
    INSERT INTO public.parser_detailed 
        (parser_id, permission_group_id, "name")
        VALUES (%(parser_id)s, %(project_id)s, %(name)s)
        ON CONFLICT (parser_id) DO NOTHING
"""


INSERT_PARSER_CSV = """
    INSERT INTO public.parser_csv 
        (parser_id, delimiter, timezone, encoding, headlines_to_exclude, footlines_to_exclude, pandas_read_csv, comment, header)
    VALUES 
        (%(parser_id)s, %(delimiter)s, %(timezone)s, %(encoding)s, %(skiprows)s, %(skipfooter)s, %(pandas_read_csv)s, %(comment)s, %(header)s)
    ON CONFLICT ("parser_id") DO NOTHING
"""

INSERT_PARSER_TS_COLUMNS = """
    INSERT INTO public.parser_csv_timestamp_column
        (parser_csv_id, "column", timestamp_format)
    VALUES
        (%(parser_csv_id)s, %(column)s, %(timestamp_format)s)
"""

SELECT_THING_AND_INGEST = """
                                    SELECT t.id,
                                           t."uuid"              AS "thing_uuid",
                                           t."name"              AS "thing_name",
                                           t.project_id,
                                           p.uuid                as "project_uuid",
                                           t.description         as thing_descriptiopn,
                                           it."name"             AS ingest_type_name,
                                           ea.id                 AS ea_id,
                                           ea.api_type_id        AS ea_api_type_id,
                                           eat."name"            AS ea_type_name,
                                           ea.sync_interval      AS ea_sync_interval,
                                           ea.sync_enabled       AS ea_sync_enabled,
                                           ea.settings           AS ea_settings,
                                           es.id                 AS es_id,
                                           es.uri                AS es_uri,
                                           es."path"             AS es_path,
                                           es."user"             AS es_user,
                                           es."password"         AS es_password,
                                           es.ssh_priv_key       AS es_ssh_priv_key,
                                           es.ssh_pub_key        AS es_ssh_pub_key,
                                           es.sync_interval      AS es_sync_interval,
                                           es.sync_enabled       AS es_sync_enabled,
                                           m.id                  AS mqtt_id,
                                           m."user"              AS mqtt_user,
                                           m."password"          AS mqtt_password,
                                           m."password_hashed"   AS mqtt_password_hashed,
                                           m.topic               AS mqtt_topic,
                                           m.mqtt_device_type_id AS mqtt_device_type_id,
                                           mdt."name"            as "mqtt_device_type_name",
                                           s3.id                 AS s3_id,
                                           s3."user"             AS s3_user,
                                           s3."password"         AS s3_password,
                                           s3.bucket             AS s3_bucket,
                                           s3.filename_pattern   AS s3_filename_pattern,
                                           fp."uuid"             as "file_parser_uuid"
                                    FROM config_db.thing t
                                             LEFT JOIN config_db.ext_api ea ON ea.id = t.ext_api_id
                                             LEFT JOIN config_db.ext_sftp es ON es.id = t.ext_sftp_id
                                             LEFT JOIN config_db.mqtt m ON m.id = t.mqtt_id
                                             LEFT JOIN config_db.s3_store s3 ON s3.id = t.s3_store_id
                                             JOIN config_db.ingest_type it ON it.id = t.ingest_type_id
                                             JOIN config_db.project p on p.id = t.project_id
                                             LEFT JOIN config_db.mqtt_device_type mdt on mdt.id = m.mqtt_device_type_id
                                             left join config_db.file_parser fp on fp.id = s3.file_parser_id 
                                             left join config_db.ext_api_type eat on eat.id = ea.api_type_id
                                    """

INSERT_INGEST = """
    INSERT INTO public.ingest ("uuid", ingest_type, "name", permission_group_id, description, parser_id)
    VALUES (%(thing_uuid)s, %(ingest_type_name)s, %(thing_name)s, %(project_id)s, %(thing_descriptiopn)s, %(parser_id)s)
    RETURNING id        
"""

INSERT_INGEST_SFTP = """
    INSERT INTO public.ingest_sftp (ingest_id, filename_pattern, username, password, bucket_name)
    VALUES (%(ingest_id)s, %(s3_filename_pattern)s, %(s3_user)s, %(s3_password)s, %(s3_bucket)s)
"""

INSERT_INGEST_EXT_SFTP = """
    INSERT INTO public.ingest_external_sftp
        (ingest_id, uri, "path", filename_pattern, username, "password", sync_interval_in_minutes, sync_enabled, ssh_private_key, ssh_public_key, bucket_name, bucket_username, bucket_password)
    VALUES
         (%(ingest_id)s, %(es_uri)s, %(es_path)s, %(s3_filename_pattern)s, %(es_user)s, %(es_password)s, %(es_sync_interval)s, %(es_sync_enabled)s, %(es_ssh_priv_key)s, %(es_ssh_pub_key)s ,%(s3_bucket)s, %(s3_user)s, %(s3_password)s)
"""

INSERT_INGEST_EXT_API = """
    INSERT INTO public.ingest_external_api (ingest_id, api_type, sync_enabled, sync_interval_in_minutes)
    VALUES  (%(ingest_id)s, %(ea_type_name)s, %(ea_sync_enabled)s, %(ea_sync_interval)s)
"""

INSERT_INGEST_TTN_API = """
    INSERT INTO public.ingest_external_api_the_things_network (ingest_id, api_key, endpoint_uri)
    VALUES (%(ingest_id)s, %(ttn_api_key)s, %(ttn_uri)s)
"""

INSERT_INGEST_DWD_API = """
    INSERT INTO public.ingest_external_api_dwd (ingest_id, station_id, period_in_minutes)
    VALUES (%(ingest_id)s, %(dwd_station_id)s, %(dwd_period)s)
"""

INSERT_INGEST_UBA_API = """
    INSERT INTO public.ingest_external_api_uba (ingest_id, station_id)
    VALUES (%(ingest_id)s, %(uba_station_id)s)
"""

INSERT_INGEST_TSYSTEMS_API = """
    INSERT INTO public.ingest_external_api_tsystems
        (ingest_id, "group", station_id, tsystems_username, tsystems_password)
    VALUES (%(ingest_id)s, %(tsystems_group)s, %(tsystems_station)s, %(tsystems_username)s, %(tsystems_password)s)
"""

INSERT_INGEST_BOSCH_API = """
    INSERT INTO public.ingest_external_api_bosch
        (ingest_id, endpoint, sensor_id, bosch_username, bosch_password, period_in_minutes)
    VALUES
        (%(ingest_id)s, %(bosch_endpoint)s, %(bosch_sensor)s, %(bosch_user)s, %(bosch_password)s, %(bosch_period)s)
"""

SELECT_QAQC = """
    SELECT q.id, q."name" as "qc_name", q.context_window, q.default, qt."function", qt.args, qt.position, qt.name as "test_name", qt.streams, p."uuid" as "project_uuid", d."schema"
    FROM config_db.qaqc q
    JOIN config_db.qaqc_test qt ON qt.qaqc_id = q.id
    join config_db.project p on p.id = q.project_id 
    JOIN config_db.database d on d.id = p.database_id
    WHERE q."name" <> 'MyConfig'
"""

INSERT_QC_SETTINGS = """
    INSERT INTO public.quality_control_setting
        (permission_group_id, "name", context_window, is_active, "uuid")
    VALUES 
        (%(project_id)s, %(qc_name)s, %(context_window)s, %(default)s, %(qc_uuid)s)
    ON CONFLICT ("uuid") DO UPDATE SET
        "name" = EXCLUDED."name",
        context_window = EXCLUDED.context_window,
        is_active = EXCLUDED.is_active    
    RETURNING id
"""

INSERT_QC_FUNCTION = """
    INSERT INTO public.quality_control_function
        (quality_control_setting_id, "name")
    VALUES (%(qc_setting_id)s, %(function)s)
    RETURNING id
"""

INSERT_QC_FUNC_ARGS = """
    INSERT INTO public.quality_control_function_argument
        (quality_control_function_id, "name", "type", "input")
    VALUES
       (%(func_id)s, %(name)s, %(type)s, %(input)s)
"""
