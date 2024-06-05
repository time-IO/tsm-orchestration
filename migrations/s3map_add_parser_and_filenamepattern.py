#!/usr/bin/env python
from __future__ import annotations

import os
import warnings

import psycopg
import sys


def has_column(cur, table, column):
    records = cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = %s "
        "and column_name = %s",
        (table, column),
    ).fetchall()
    return len(records) > 0


ALTER_TABLE_SQL = (
    "ALTER TABLE s3map.mapping "
    "ADD COLUMN filename_pattern varchar(256), "
    "ADD COLUMN parser varchar(256)"
)
FETCH_THING_IDS = "SELECT distinct thing_uuid FROM s3map.mapping"
FETCH_THING_IDS2 = "SELECT distinct thing_uuid FROM mapping"

GET_PATTERN_PARSER_BY_THING_ID = ()


usage = f"""{os.path.basename(__file__)} S3_DSN FE_DSN

Adds columns 'filename_pattern' and 'parser' to s3map.mapping
and fills them with data from the frontend.

    S3_DSN  is the full fledged database connection string to 
            the s3map_db with ** admin privileges ** (alter tables).

    FE_DB   is the full fledged database connection string to 
            the frontenddb (read)

Example:
    S3DB=postgresql://postgres:postgres@localhost/postgres
    FEDB=postgresql://frontenddb:frontenddb@localhost/postgres
    python {os.path.basename(__file__)} $S3DB $FEDB
"""


def get_parser_and_pattern(cur, thing_id):
    return cur.execute(
        "SELECT pt.name, th.sftp_filename_pattern FROM tsm_thing th "
        "JOIN tsm_thing_parser t2p ON th.id = t2p.thing_id "
        "JOIN tsm_parser p ON t2p.parser_id = p.id "
        "JOIN tsm_parsertype pt on p.type_id = pt.id "
        "WHERE th.thing_id = %s",
        (thing_id,),
    ).fetchone()


def update_parser_and_pattern(cur, thing_id, parser, pattern):
    cur.execute(
        "UPDATE s3map.mapping SET "
        "filename_pattern = %s, "
        "parser = %s "
        "WHERE thing_uuid = %s",
        (pattern, parser, thing_id),
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(usage)
        sys.exit(1)

    with psycopg.connect(sys.argv[1]) as s3, psycopg.connect(sys.argv[2]) as fe:
        early_exit = False
        with s3.cursor() as c:
            for col in ["filename_pattern", "parser"]:
                if has_column(c, "mapping", col):
                    warnings.warn(
                        f"column {col!r} already exist in table s3map.mapping"
                    )
                    early_exit = True
        if early_exit:
            sys.exit(0)

        with s3.cursor() as wc, fe.cursor() as rc:
            wc.execute(ALTER_TABLE_SQL)
            thing_ids = wc.execute(FETCH_THING_IDS).fetchall()
            for thing_id in thing_ids:
                thing_id = thing_id[0]
                pp = get_parser_and_pattern(rc, thing_id)
                if pp is None:
                    par = pat = None
                else:
                    par, pat = pp
                update_parser_and_pattern(wc, thing_id, par, pat)
            s3.commit()
