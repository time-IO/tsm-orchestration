from sqlmodel import SQLModel, Field, Index, func, Column, Relationship
from typing import Optional
from datetime import datetime, timezone
from .parser import Parser, ParserRead


class ParserDetailedRead(ParserRead):
    created_at: datetime
    name: str
    permission_group_id: int
    description: Optional[str]
    created_by_id: Optional[int]

    permission_group: dict


class ParserDetailedCreate(SQLModel):
    name: str
    permission_group_id: int
    description: Optional[str] = None


class ParserDetailedUpdate(SQLModel):
    # it's currently not possible to change the permission group
    name: Optional[str] = None
    description: Optional[str] = None


class ParserDetailed(SQLModel, table=True):
    __tablename__ = "parser_detailed"

    __table_args__ = (
        Index(
            "ix_parser_name_permission_group",
            func.lower(Column("name")),
            Column("permission_group_id"),
            unique=True,
        ),
    )

    parser_id: int = Field(
        foreign_key="parser.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    permission_group_id: int = Field(foreign_key="permission_group.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by_id: Optional[int] = None
    name: str
    description: Optional[str] = None

    # Relationship to permission group
    permission_group: "PermissionGroup" = Relationship(back_populates="parser_detailed")

    # Relationships
    parser: Parser = Relationship(back_populates="parser_detailed")

    parser_csv: Optional["ParserCsv"] = Relationship(
        back_populates="parser_detailed", cascade_delete=True
    )

    @property
    def mqtt_information(self):
        if self.parser_csv is not None:
            return self.parser_csv.mqtt_information

        return None

    @property
    def parser_info(self):
        return {"name": self.name}
