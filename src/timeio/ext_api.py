import requests
import json

from timeio.feta import Thing
from timeio.common import get_envvar
from timeio.journaling import Journal
from timeio.mqtt import publish_single

api_base_url = get_envvar("DB_API_BASE_URL")

def write_observations(thing: Thing, parsed_observations: dict):
    journal = Journal(f"SYNC_{thing.ext_api.api_type_name}")
    resp = requests.post(
        f"{api_base_url}/observations/upsert/{thing.uuid}",
        json=parsed_observations,
        headers={"Content-Type": "application/json"},
    )
    if resp.status_code != 200:
        journal.error(f"Failed to insert data into timeIO DB: {resp.text}", thing.uuid)
        resp.raise_for_status()
        # exit

    journal.info(
        f"Successfully inserted {len(parsed_observations['observations'])} "
        f"observations for thing {thing.uuid} into timeIO DB",
        thing.uuid,
    )
    publish_single("data_parsed", json.dumps({"thing_uuid": thing.uuid}))
