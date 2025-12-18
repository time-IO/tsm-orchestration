UPSERT_RAWDATASTORAGE = """
        INSERT INTO thing_management_db.rawdatastorage
            (thing_id, "user", "password", bucket_name, file_name_pattern, file_parser_id)
        VALUES (%(thing_id)s, %(s3_user)s, %(s3_password)s, %(s3_bucket)s, %(s3_filename_pattern)s, %(file_parser_id)s)
        ON CONFLICT (thing_id) DO UPDATE SET
            "user"            = EXCLUDED."user",
            "password"        = EXCLUDED."password",
            bucket_name       = EXCLUDED.bucket_name,
            file_name_pattern = EXCLUDED.file_name_pattern,
            file_parser_id    = EXCLUDED.file_parser_id
        """

INGEST_QUERIES = {
    "extapi": """
        INSERT INTO thing_management_db.external_api_ingest
            (thing_id, api_type_id, sync_interval, sync_enabled, settings)
        VALUES (%(thing_id)s, %(ea_api_type_id)s, %(ea_sync_interval)s, %(ea_sync_enabled)s, %(ea_settings)s)
        ON CONFLICT (thing_id) DO UPDATE SET 
            sync_interval = EXCLUDED.sync_interval,
            sync_enabled  = EXCLUDED.sync_enabled,
            settings      = EXCLUDED.settings,
            api_type_id   = EXCLUDED.api_type_id
        """,
    "extsftp": """
        INSERT INTO thing_management_db.external_sftp_ingest
            (thing_id, uri, path, "user", "password", ssh_priv_key, ssh_pub_key, sync_interval, sync_enabled)
        VALUES (%(thing_id)s, %(es_uri)s, %(es_path)s, %(es_user)s, %(es_password)s,
                %(es_ssh_priv_key)s, %(es_ssh_pub_key)s, %(es_sync_interval)s, %(es_sync_enabled)s)
        ON CONFLICT (thing_id) DO UPDATE SET 
            uri           = EXCLUDED.uri,
            path          = EXCLUDED.path,
            "user"        = EXCLUDED."user",
            "password"    = EXCLUDED."password",
            ssh_priv_key  = EXCLUDED.ssh_priv_key,
            ssh_pub_key   = EXCLUDED.ssh_pub_key,
            sync_interval = EXCLUDED.sync_interval,
            sync_enabled  = EXCLUDED.sync_enabled
        """,
    "mqtt": """
        INSERT INTO thing_management_db.mqtt_ingest
            (thing_id, "user", "password", password_hashed, topic, mqtt_device_type_id)
        VALUES (%(thing_id)s, %(mqtt_user)s, %(mqtt_password)s, %(mqtt_password_hashed)s,
                %(mqtt_topic)s, %(mqtt_device_type_id)s)
        ON CONFLICT (thing_id) DO UPDATE SET 
            "user"            = EXCLUDED."user",
            "password"        = EXCLUDED."password",
            "password_hashed" = EXCLUDED.password_hashed,
            topic             = EXCLUDED.topic
        """,
    "sftp": UPSERT_RAWDATASTORAGE,
}

SELECT_PROJECT_AND_DB = """
    SELECT p."name"      AS "project_name",
        p.uuid        AS "project_uuid",
        p.database_id AS "project_database_id",
        db.schema,
        db."user",
        db."password",
        db.ro_user,
        db.ro_password
    FROM config_db.project p
    JOIN config_db.database db ON p.database_id = db.id
"""

INSERT_DB = """
    INSERT INTO thing_management_db.database (db_schema, "user", "password", ro_user, ro_password)
    VALUES (%(schema)s, %(user)s, %(password)s, %(ro_user)s, %(ro_password)s)
    RETURNING id
"""
INSERT_PROJECT = """
    INSERT INTO thing_management_db.project ("name", uuid, database_id)
    VALUES (%(project_name)s, %(project_uuid)s, %(project_database_id)s); \
"""

GET_PARSER = """
    SELECT fp.file_parser_type_id,
        fp."name",
        fp.params,
        fp."uuid"  AS "parser_uuid",
        t.uuid   AS "thing_uuid",
        p."uuid" AS "project_uuid"
    FROM config_db.file_parser fp
    JOIN config_db.s3_store s3 ON s3.file_parser_id = fp.id
    JOIN config_db.thing t ON t.s3_store_id = s3.id
    JOIN config_db.project p ON p.id = t.project_id
"""

UPSERT_PARSER = """
    INSERT INTO thing_management_db.file_parser
        (file_parser_type_id, project_id, "name", settings, created_by, "uuid")
    VALUES (%(file_parser_type_id)s, %(project_id)s, %(name)s, %(params)s, %(created_by)s, %(parser_uuid)s)
    ON CONFLICT (project_id, "name") DO UPDATE SET 
        settings = EXCLUDED.settings,
        "uuid" = EXCLUDED."uuid"
"""

SELECT_THING_AND_INGEST = """
    SELECT t.id,
        t."uuid",
        t."name",
        t.project_id,
        p.uuid                AS "project_uuid",
        t.ingest_type_id,
        t.description,
        it."name"             AS ingest_type_name,
        ea.id                 AS ea_id,
        ea.api_type_id        AS ea_api_type_id,
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
        mdt."name"            AS "mqtt_device_type_name",
        s3.id                 AS s3_id,
        s3."user"             AS s3_user,
        s3."password"         AS s3_password,
        s3.bucket             AS s3_bucket,
        s3.filename_pattern   AS s3_filename_pattern,
        fp."uuid"             AS "file_parser_uuid"
    FROM config_db.thing t
    LEFT JOIN config_db.ext_api ea ON ea.id = t.ext_api_id
    LEFT JOIN config_db.ext_sftp es ON es.id = t.ext_sftp_id
    LEFT JOIN config_db.mqtt m ON m.id = t.mqtt_id
    LEFT JOIN config_db.s3_store s3 ON s3.id = t.s3_store_id
    JOIN config_db.ingest_type it ON it.id = t.ingest_type_id
    JOIN config_db.project p ON p.id = t.project_id
    LEFT JOIN config_db.mqtt_device_type mdt ON mdt.id = m.mqtt_device_type_id
    LEFT JOIN config_db.file_parser fp ON fp.id = s3.file_parser_id
"""

UPSERT_THING = """
    INSERT INTO thing_management_db.thing
        (uuid, "name", description, project_id, ingest_type_id, created_by)
    VALUES (%(uuid)s, %(name)s, %(description)s, %(project_id)s, %(ingest_type_id)s, %(created_by)s)
    ON CONFLICT (uuid) DO UPDATE SET
        "name"           = EXCLUDED."name",
        "description"    = EXCLUDED."description",
        "ingest_type_id" = EXCLUDED."ingest_type_id"
    RETURNING id
"""
