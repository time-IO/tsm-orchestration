from enum import Enum


class IngestType(str, Enum):
    EXTERNAL_API = "external_api"
    SFTP = "sftp"
    MQTT = "mqtt"
    EXTERNAL_SFTP = "external_sftp"

    @classmethod
    def from_string(cls, value: str) -> "IngestType":
        """
        Case‑insensitive lookup of an IngestType member by its string value.

        Raises
        ------
        ValueError
            If ``value`` does not match any known ingest‑type string.
        """
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")

    def __str__(self) -> str:
        """Return the underlying string representation."""
        return self.value


class ApiType(str, Enum):
    BOSCH = "bosch"
    DWD = "dwd"
    NEUTRON_MONITOR = "nm"
    THE_THINGS_NETWORK = "ttn"
    TSYSTEMS = "tsystems"
    UBA = "uba"
    SENSOTO = "sensoto"

    @classmethod
    def from_string(cls, value: str) -> "ApiType":
        """
        Case‑insensitive lookup of an IngestType member by its string value.

        Raises
        ------
        ValueError
            If ``value`` does not match any known api-type string.
        """
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")

    def __str__(self) -> str:
        """Return the underlying string representation."""
        return self.value


class ParserType(str, Enum):
    CSV = "csv"
    MQTT = "mqtt"
    JSON = "json"
    SOILCAN = "soilcan"

    @classmethod
    def from_string(cls, value: str) -> "ParserType":
        """
        Case‑insensitive lookup of an IngestType member by its string value.

        Raises
        ------
        ValueError
            If ``value`` does not match any known parser-type string.
        """
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")

    def __str__(self) -> str:
        """Return the underlying string representation."""
        return self.value
