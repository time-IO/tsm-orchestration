#!/usr/bin/python3

from sync_utils import (
    create_table,
    upsert_table,
    get_connection_from_env,
)
import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))

file_names = [
    "sms_configuration.json",
    "sms_configuration_contact_role.json",
    "sms_configuration_dynamic_location_begin_action.json",
    "sms_configuration_static_location_begin_action.json",
    "sms_contact.json",
    "sms_datastream_link.json",
    "sms_device.json",
    "sms_device_contact_role.json",
    "sms_device_mount_action.json",
    "sms_device_property.json",
]

file_path_list = [os.path.join(script_dir, "tables", file_name) for file_name in file_names]

if __name__ == "__main__":
    url = os.environ.get("SMS_API_URL")
    home = os.environ.get("HOME")
    os.chdir(home)
    for file_path in file_path_list:
        db = get_connection_from_env()
        try:
            with db:
                with db.cursor() as c:
                    with open(file_path, "r") as f:
                        table_dict = json.load(f)
                    create_table(c=c, table_dict=table_dict)
                    upsert_table(c=c, url=url, table_dict=table_dict)
        finally:
            db.close()
