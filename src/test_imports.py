#!/usr/bin/env python3

# test if we can import everything without
# errors, but we ignore warnings
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from mqtt.base_handler import *  # noqa
    from setup_crontab import *  # noqa
    from databases import *  # noqa
    from setup_user_database import *  # noqa
    from run_file_ingest import *  # noqa
    from src.timeio.frost.frost import *  # noqa
    from setup_frost import *  # noqa
    from setup_grafana_dashboard import *  # noqa
    from setup_grafana_user import *  # noqa
    from setup_minio import *  # noqa
    from run_mqtt_ingest import *  # noqa
    from setup_mqtt_user import *  # noqa
    from parsing import *  # noqa
    from thing import *  # noqa
    from version import __version__

if __name__ == "__main__":
    print(__version__)
