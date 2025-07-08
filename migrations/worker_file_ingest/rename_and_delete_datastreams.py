#!/usr/bin/env python3

from __future__ import annotations
import click
import glob
import yaml
import psycopg
from psycopg import sql


@click.command()
@click.argument("thing_uuid", type=str)
@click.argument(
    "dsn", type=str, default="postgresql://postgres:postgres@localhost:5432/postgres"
)
def update_datastreams(thing_uuid, dsn) -> None:
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            schema = get_thing_schema(cur, thing_uuid)
            set_search_path(cur, schema)
            drop_datastream_pos_constaint(cur)
            datastreams = get_datastreams_from_yaml(thing_uuid)
            print(datastreams)
            ds_name_ids = []
            for ds_pos, ds_name in datastreams.items():
                try:
                    ds_name_ids.append(get_datastream_id(cur, thing_uuid, ds_pos))
                    print(f"Renaming datastream at position {ds_pos} to {ds_name}")
                    rename_datastream(cur, thing_uuid, ds_pos, ds_name)
                except ValueError:
                    print(f"Datastream at position {ds_pos} not found, skipping.")
            for ds_id in ds_name_ids:
                delete_datastream_observations(cur, thing_uuid, ds_id)
                delete_datastream(cur, thing_uuid, ds_id)
    # Open new connection to commit previous changes
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            set_search_path(cur, schema)
            add_datastream_pos_constraint(cur)


def get_thing_schema(cur, thing_uuid: str) -> str:
    query = sql.SQL(
        "SELECT schema FROM schema_thing_mapping WHERE thing_uuid = {thing_uuid}"
    ).format(thing_uuid=sql.Literal(thing_uuid))
    cur.execute(query)
    return cur.fetchone()[0]


def set_search_path(cur, schema: str) -> None:
    identifier = sql.Identifier(schema)
    query = sql.SQL("SET search_path TO {}").format(identifier)
    cur.execute(query)


def get_datastreams_from_yaml(thing_uuid: str) -> dict:
    match = glob.glob(f"datastream_mapping/{thing_uuid}.yaml")
    if not match:
        raise FileNotFoundError(f"No YAML file found for thing UUID: {thing_uuid}")
    with open(match[0], "r") as file:
        ds_mapping = yaml.safe_load(file)
    return ds_mapping.get(thing_uuid)


def get_thing_name(cur, thing_uuid: str) -> str:
    query = sql.SQL("SELECT name FROM thing WHERE uuid = {thing_uuid}").format(
        thing_uuid=sql.Literal(thing_uuid)
    )
    cur.execute(query)
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        raise ValueError(f"No thing found with UUID: {thing_uuid}")


def get_datastream_id(cur, thing_uuid: str, ds_pos: int) -> int:
    query = sql.SQL(
        "SELECT d.id FROM datastream d "
        "JOIN thing t ON d.thing_id = t.id "
        "WHERE t.uuid = {thing_uuid} "
        "AND d.position = {ds_pos}::text"
    ).format(thing_uuid=sql.Literal(thing_uuid), ds_pos=sql.Literal(ds_pos))
    cur.execute(query)
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        raise ValueError(
            f"No datastream found for UUID: {thing_uuid} at position: {ds_pos}"
        )


def rename_datastream(cur, thing_uuid: str, ds_pos: int, ds_name: str) -> None:
    ## Drop the unique constraint temporarily
    cur.execute(
        "ALTER TABLE datastream "
        "DROP CONSTRAINT IF EXISTS datastream_thing_id_position_9f2cfe68_uniq"
    )
    thing_name = get_thing_name(cur, thing_uuid)
    ds_name_new = f"{thing_name}/{ds_name}"
    ds_pos_new = ds_name

    query = sql.SQL(
        "UPDATE datastream d "
        "SET name = {name_new}, position = {pos_new} "
        "FROM thing t "
        "WHERE d.thing_id = t.id "
        "AND t.uuid = {thing_uuid} "
        "AND d.position = {pos_old}::text",
    ).format(
        name_new=sql.Literal(ds_name_new),
        pos_new=sql.Literal(ds_pos_new),
        thing_uuid=sql.Literal(thing_uuid),
        pos_old=sql.Literal(ds_pos),
    )
    print(query.as_string())
    cur.execute(query)


def delete_datastream_observations(cur, thing_uuid: str, ds_id: int) -> None:
    query = sql.SQL(
        "DELETE FROM observation o "
        "USING datastream d "
        "JOIN thing t ON d.thing_id = t.id "
        "WHERE o.datastream_id = d.id "
        "AND t.uuid = {thing_uuid} "
        "AND d.id = {ds_id}"
    ).format(
        thing_uuid=sql.Literal(thing_uuid),
        ds_id=sql.Literal(ds_id),
    )
    print(query.as_string())
    cur.execute(query)


def delete_datastream(cur, thing_uuid: str, ds_id: int) -> None:
    query = sql.SQL(
        "DELETE FROM datastream d "
        "USING thing t "
        "WHERE d.thing_id = t.id "
        "AND t.uuid = {thing_uuid} "
        "AND d.id = {ds_id}"
    ).format(
        thing_uuid=sql.Literal(thing_uuid),
        ds_id=sql.Literal(ds_id),
    )
    print(query.as_string())
    cur.execute(query)


def drop_datastream_pos_constaint(cur) -> None:
    cur.execute(
        "ALTER TABLE datastream "
        "DROP CONSTRAINT IF EXISTS datastream_thing_id_position_9f2cfe68_uniq"
    )
    print("Dropped unique constraint on thing_id and position in datastream table.")


def add_datastream_pos_constraint(cur) -> None:
    cur.execute(
        "ALTER TABLE datastream "
        "ADD CONSTRAINT datastream_thing_id_position_9f2cfe68_uniq "
        "UNIQUE (thing_id, position)"
    )
    print("Added unique constraint on thing_id and position in datastream table.")


# need to either rename new datastream or drop constraint on id, position before renaming
# need to get datastream_ids that should be deleted before renaming
#

if __name__ == "__main__":
    update_datastreams()
