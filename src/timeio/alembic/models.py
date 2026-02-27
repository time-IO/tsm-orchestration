from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    Text,
    UniqueConstraint,
    VARCHAR,
)
from sqlalchemy.dialects.postgresql import JSONB, DOUBLE_PRECISION, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Thing(Base):
    __tablename__ = "thing"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(VARCHAR(200), nullable=False)
    uuid: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    properties: Mapped[dict | None] = mapped_column(JSONB)


class Journal(Base):
    __tablename__ = "journal"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    level: Mapped[str] = mapped_column(VARCHAR(30), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    extra: Mapped[dict | None] = mapped_column(JSONB)
    thing_id: Mapped[int] = mapped_column(
        ForeignKey("thing.id", deferrable=True, initially="DEFERRED"), nullable=False
    )
    origin: Mapped[str | None] = mapped_column(VARCHAR(200))


class Datastream(Base):
    __tablename__ = "datastream"
    __table_args__ = (
        UniqueConstraint(
            "thing_id", "position", name="datastream_thing_id_position_uniq"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(VARCHAR(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    properties: Mapped[dict | None] = mapped_column(JSONB)
    position: Mapped[str] = mapped_column(VARCHAR(200), nullable=False)
    thing_id: Mapped[int] = mapped_column(
        ForeignKey("thing.id", deferrable=True, initially="DEFERRED"), nullable=False
    )


class Observation(Base):
    __tablename__ = "observation"
    __table_args__ = (
        UniqueConstraint(
            "datastream_id",
            "result_time",
            name="observation_datastream_id_result_time_uniq",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    phenomenon_time_start: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True)
    )
    phenomenon_time_end: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True)
    )
    result_time: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    result_type: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    result_number: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    result_string: Mapped[str | None] = mapped_column(VARCHAR(200))
    result_json: Mapped[dict | None] = mapped_column(JSONB)
    result_boolean: Mapped[bool | None] = mapped_column(Boolean)
    result_latitude: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    result_longitude: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    result_altitude: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    result_quality: Mapped[dict | None] = mapped_column(JSONB)
    valid_time_start: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    valid_time_end: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    parameters: Mapped[dict | None] = mapped_column(JSONB)
    datastream_id: Mapped[int] = mapped_column(
        ForeignKey("datastream.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )


class RelationRole(Base):
    __tablename__ = "relation_role"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(VARCHAR(200), nullable=False, unique=True)
    definition: Mapped[str | None] = mapped_column(Text)
    inverse_name: Mapped[str] = mapped_column(VARCHAR(200), nullable=False, unique=True)
    inverse_definition: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    properties: Mapped[dict | None] = mapped_column(JSONB)


class RelatedDatastream(Base):
    __tablename__ = "related_datastream"
    __table_args__ = (
        UniqueConstraint(
            "datastream_id",
            "role_id",
            "target_id",
            name="related_datastream_datastream_id_role_id_target_id_uniq",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    datastream_id: Mapped[int] = mapped_column(
        ForeignKey("datastream.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("relation_role.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )
    target_id: Mapped[int] = mapped_column(
        ForeignKey("datastream.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
    )


class MqttMessage(Base):
    __tablename__ = "mqtt_message"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    thing_id: Mapped[int] = mapped_column(
        ForeignKey("thing.id", deferrable=True, initially="DEFERRED"), nullable=False
    )


Index("journal_thing_id", Journal.thing_id)
Index("datastream_thing_id", Datastream.thing_id)
Index("idx_observation_result_time", Observation.result_time)
