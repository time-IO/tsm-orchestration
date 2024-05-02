#!/user/bin/python3

from sync_utils import (
    create_table,
    upsert_table,
    get_connection_from_env,
)
import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))

file_names = [
    "sms_cv_measured_quantity.json"
]

file_path_list = [os.path.join(script_dir, "tables", file_name) for file_name in file_names]

if __name__ == "__main__":
    url = os.environ.get("CV_API_URL")
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
                    upsert_table(c=db.cursor(), url=url, table_dict=table_dict)
        finally:
            db.close()
