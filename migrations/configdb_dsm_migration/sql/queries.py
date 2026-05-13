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
    INSERT INTO dsm_db.permission_group ("name", uuid, entitlement)
    VALUES (%(project_name)s, %(project_uuid)s, %(project_name)s)
    RETURNING id
"""

INSERT_DB = """
    INSERT INTO dsm_db.database (permission_group_id, "username", "password", read_only_username, read_only_password, "url", "name")
    VALUES (%(project_id)s, %(user)s, %(password)s, %(ro_user)s, %(ro_password)s, %(url)s, 'dummy')
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
    INSERT INTO dsm_db.parser (uuid, parser_type) VALUES (%(parser_uuid)s, 'csv')
    ON CONFLICT (uuid)
    DO UPDATE SET
        parser_type = EXCLUDED.parser_type
    RETURNING id
"""
INSERT_PARSER_DETAILED = """
    INSERT INTO dsm_db.parser_detailed 
        (parser_id, permission_group_id, "name")
        VALUES (%(parser_id)s, %(project_id)s, %(name)s)
        ON CONFLICT (parser_id)
        DO UPDATE SET
            name = EXCLUDED.name
"""


INSERT_PARSER_CSV = """
    INSERT INTO dsm_db.parser_csv 
        (parser_id, delimiter, timezone, encoding, headlines_to_exclude, footlines_to_exclude, pandas_read_csv, comment, header)
    VALUES 
        (%(parser_id)s, %(delimiter)s, %(timezone)s, %(encoding)s, %(skiprows)s, %(skipfooter)s, %(pandas_read_csv)s, %(comment)s, %(header)s)
    ON CONFLICT ("parser_id") 
    DO UPDATE SET
        delimiter = EXCLUDED.delimiter,
        timezone = EXCLUDED.timezone,
        encoding = EXCLUDED.encoding,
        headlines_to_exclude = EXCLUDED.headlines_to_exclude,
        footlines_to_exclude = EXCLUDED.footlines_to_exclude,
        pandas_read_csv = EXCLUDED.pandas_read_csv,
        comment = EXCLUDED.comment,
        header = EXCLUDED.header
"""

INSERT_PARSER_TS_COLUMNS = """
    INSERT INTO dsm_db.parser_csv_timestamp_column
        (parser_csv_id, "column", timestamp_format)
    VALUES
        (%(parser_csv_id)s, %(column)s, %(timestamp_format)s)
"""
