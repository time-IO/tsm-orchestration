import os
import sys

import psycopg

QUERY = """
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sms_datastream_link' 
        AND column_name = 'thing_name'
    ) THEN
        ALTER TABLE sms_datastream_link ADD COLUMN thing_name varchar(256);
    END IF;
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sms_datastream_link' 
        AND column_name = 'datastream_name'
    ) THEN
        ALTER TABLE sms_datastream_link ADD COLUMN datastream_name varchar(256);
    END IF;
END $$;
"""

usage = f"""{os.path.basename(__file__)} DB_URL

Add the columns 'thing_name' and 'datastream_name' to the foreign table 'sms_datastream_link'

    DB_URL is the connection string of the respective database

Example:
    python {os.path.basename(__file__)} postgresql://postgres:postgres@localhost:5432/postgres
"""

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(usage)
        sys.exit(1)

    with psycopg.connect(sys.argv[1]) as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(QUERY)
            except Exception as error:
                conn.rollback()
                print(f"Failed to add columns to sms_datastream_link: {error}")
                sys.exit(1)
