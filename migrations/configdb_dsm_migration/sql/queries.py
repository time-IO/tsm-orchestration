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
    INSERT INTO public.database (permission_group_id, "username", "password", read_only_username, read_only_password, "url", "name")
    VALUES (%(project_id)s, %(user)s, %(password)s, %(ro_user)s, %(ro_password)s, %(url)s, 'dummy')
"""
