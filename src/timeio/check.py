#!/usr/bin/env python3

# test if we can import everything without
# errors, but we ignore warnings
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from base_handler import *  # noqa
    from crontab_setup import *  # noqa
    from databases import *  # noqa
    from db_setup import *  # noqa
    from file_ingest import *  # noqa
    from frost import *  # noqa
    from frost_setup import *  # noqa
    from grafana_dashboard_setup import *  # noqa
    from grafana_user_setup import *  # noqa
    from minio_setup import *  # noqa
    from mqtt_ingest import *  # noqa
    from mqtt_user_setup import *  # noqa
    from parsing import *  # noqa
    from thing import *  # noqa
    from version import __version__

if __name__ == "__main__":
    print(__version__)
