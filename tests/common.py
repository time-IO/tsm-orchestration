#!/usr/bin/env python3

import os
from typing import Any

no_default = type("no_default", (), {})


def getenv_bool(
    name, false_list=("no", "false", "0", "null", "none"), empty_is_False: bool = False
) -> bool:
    """
    Return True if an environment variable is set and its value
    is not in the false_list.
    Return False if an environment variable is unset or if its value
    is in the false_list.

    If 'empty_is_False' is True:
        Same logic as above, but an empty string is considered False

    The false_list not case-sensitive. (faLsE == FALSE = false)
    """
    val = os.environ.get(name, None)
    if val is None:
        return False
    if val == "":
        return not empty_is_False
    return val.lower() not in false_list


def getenv(name, default: Any = no_default, cast_to: type = None, cast_None=True):
    val = os.environ.get(name)
    if val is None:
        if default is no_default:
            raise EnvironmentError(f"Missing environment variable {name!r}.")
        return default
    elif val == "None" and cast_None:
        return None
    elif cast_to is not None:
        try:
            if cast_to is bool:
                return getenv_bool(name)
            return cast_to(val)
        except Exception:
            raise TypeError(
                f"Could not cast environment variable {name!r} "
                f"to {cast_to}. Value: {val}"
            ) from None
    return val


def mk_dsn(protocol, host, usr=None, pw=None, port=None, sub=None):
    """
    Generate a string like this:
        protocol://[usr[:pw]@]host[:port][/sub]

    Examples:
        >>> mk_dsn("postgresql", "localhost")
        "postgresql://localhost"

        >>> mk_dsn("postgresql", "localhost", port=5432)
        "postgresql://localhost:5432"

        >>> mk_dsn("postgresql", "localhost", "admin")
        "postgresql://admin@localhost"

        >>> mk_dsn("postgresql", "localhost", "admin", "secret", 5432)
        "postgresql://admin:secret@localhost:5432"

        >>> mk_dsn("postgresql", "localhost", "admin", sub="DB")
        "postgresql://admin@localhost/DB"

        >>> mk_dsn("postgresql", "localhost", "admin", "secret", 5432, "DB")
        "postgresql://admin:secret@localhost:5432/DB"
    """
    if usr is None and pw is not None:
        raise ValueError("Argument 'usr' must not be None, if argument 'pw' is given.")
    if port is not None:
        host = f"{host}:{port}"
    if sub is not None:
        host = f"{host}/{sub}"
    if usr is not None:
        host = f"{usr}@{host}"
        if pw is not None:
            host = f"{pw}:{host}"
    return f"{protocol}://{host}"


def mk_postgres_dsn(usr, pw, host, port, db):
    return mk_dsn(f"postgresql", host, usr, pw, port, db)


