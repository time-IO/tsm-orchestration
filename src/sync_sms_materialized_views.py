import psycopg
from os import environ
from psycopg import connection
from datetime import datetime
import time

def get_utc_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S (UTC)")

def get_connection_from_env(retries: int = 4, sleep: int = 3) -> connection:
    user = environ.get("CREATEDB_POSTGRES_USER")
    password = environ.get("CREATEDB_POSTGRES_PASSWORD")
    host = environ.get("CREATEDB_POSTGRES_HOST")
    db = environ.get("CREATEDB_POSTGRES_DATABASE")
    err = None
    for _ in range(retries):
        try:
            return psycopg.connect(
                database=db, user=user, password=password, host=host
            )
        except Exception as e:
            err = e
            print(f"{get_utc_str()}: Retrying...")
            time.sleep(sleep)
    raise RuntimeError(f"Could not connect to database") from err

def update_materialized_views() -> None:
  conn: connection = get_connection_from_env()
  try:
      # Create a cursor object to execute SQL queries
      with conn.cursor() as cur:
          # Query to get the list of materialized views starting with the prefix "sms_"
          cur.execute("""
              SELECT matviewname
              FROM pg_matviews
              WHERE schemaname = 'public'
              AND matviewname LIKE 'sms_%'
          """)

          # Fetch the list of materialized views
          matviews = cur.fetchall()

          # Iterate over the materialized views and refresh them
          for matview in matviews:
              view_name = matview[0]
              cur.execute(f"REFRESH MATERIALIZED VIEW {view_name};")
              print(f"Refreshed materialized view: {view_name}")

      # Commit the changes
      conn.commit()

  except psycopg.Error as e:
      print(f"Error occurred: {e}")
      if conn:
          conn.rollback()

  finally:
      # Close the connection
      if conn:
          conn.close()

if __name__ == "__main__":
    update_materialized_views()