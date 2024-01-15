from sync_utils import (
    create_table,
    upsert_table,
    get_connection_from_env,
)
from os import chdir, environ
import json

url = environ.get("CV_API_URL")
home = environ.get("HOME")
chdir(home)

file_path_list = ["scripts/sms_sync/tables/sms_cv_measured_quantity.json"]

if __name__ == "__main__":
    for file_path in file_path_list:
        db = get_connection_from_env()
        try:
            with db:
                with db.cursor() as c:
                    with open(file_path, "r") as f:
                        table_dict = json.load(f)
                    create_table(c=c, table_dict=table_dict)
                    upsert_table(c=db.cursor(), url=url, table_dict=table_dict)
            print("Done!")
        finally:
            db.close()
