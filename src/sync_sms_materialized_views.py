#!/usr/bin/python3

import psycopg
from psycopg import sql

from timeio.databases import Database
from timeio.common import get_envvar

import logging

logger = logging.getLogger("sync_sms_materialized_views")


class SyncSmsMaterializedViews:
    def __init__(self):
        self.db = Database(get_envvar("DATABASE_DSN"))
        self.materialized_views = []

    def collect_materialized_views(self):
        with self.db.connection() as conn:
            try:
                with conn.cursor() as cur:
                    # Query to get the list of materialized views starting with the prefix "sms_"
                    cur.execute(
                        """
                                     SELECT matviewname
                                     FROM pg_matviews
                                     WHERE schemaname = 'public'
                                     AND matviewname LIKE 'sms_%'
                                 """
                    )

                    self.materialized_views = cur.fetchall()

                    return self
            except psycopg.Error as e:
                logger.error(f"Error occurred during fetching materialized : {e}")
                if conn:
                    conn.rollback()

    def update_materialized_views(self) -> None:
        with self.db.connection() as conn:
            try:
                # Create a cursor object to execute SQL queries
                with conn.cursor() as cur:

                    # Iterate over the materialized views and refresh them
                    for matview in self.materialized_views:
                        view_name = matview[0]
                        cur.execute(
                            sql.SQL("REFRESH MATERIALIZED VIEW {}").format(
                                sql.Identifier(view_name)
                            )
                        )
                        logger.info(f"Refreshed materialized sms view: {view_name}")

                # Commit the changes
                conn.commit()

            except psycopg.Error as e:
                logger.error(f"Error occurred during refreshing materialized : {e}")
                if conn:
                    conn.rollback()

            finally:
                # Close the connection
                if conn:
                    conn.close()


if __name__ == "__main__":
    SyncSmsMaterializedViews().collect_materialized_views().update_materialized_views()
