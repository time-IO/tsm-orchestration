from sqlmodel import SQLModel, Field, Relationship, Column, Index, func, JSON, column
import uuid as uuid_pkg
from typing import Optional
from datetime import datetime, timezone
from .permission_group import PermissionGroup
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class QualityControlFunctionArgumentBase(SQLModel):
    quality_control_function_id: int = Field(
        foreign_key="quality_control_function.id", ondelete="CASCADE"
    )
    name: str
    type: str
    input: dict = Field(sa_column=Column(JSON), default_factory=dict)


class QualityControlFunctionArgumentCreate(SQLModel):
    name: str
    type: str
    input: dict


class QualityControlFunctionArgumentUpdate(SQLModel):
    name: str | None = None
    type: str | None = None
    input: dict | None = None


class QualityControlFunctionArgumentPublic(SQLModel):
    id: int
    name: str
    type: str
    input: dict


class QualityControlFunctionArgument(QualityControlFunctionArgumentBase, table=True):
    __tablename__ = "quality_control_function_argument"

    id: int | None = Field(default=None, primary_key=True)
    quality_control_function: "QualityControlFunction" = Relationship(
        back_populates="quality_control_function_arguments"
    )


class QualityControlFunctionBase(SQLModel):
    quality_control_setting_id: int = Field(
        foreign_key="quality_control_setting.id", ondelete="CASCADE"
    )
    name: str
    label: str | None = None


class QualityControlFunctionCreate(SQLModel):
    name: str
    label: str | None = None
    quality_control_function_arguments: list[QualityControlFunctionArgumentCreate]


class QualityControlFunctionUpdate(SQLModel):
    name: str | None = None
    label: str | None = None
    quality_control_function_arguments: (
        list[QualityControlFunctionArgumentUpdate] | None
    ) = None


class QualityControlFunctionPublic(SQLModel):
    id: int
    name: str
    label: str | None = None
    quality_control_function_arguments: list[QualityControlFunctionArgumentPublic]


class QualityControlFunction(QualityControlFunctionBase, table=True):
    __tablename__ = "quality_control_function"

    id: int | None = Field(default=None, primary_key=True)
    quality_control_setting: "QualityControlSetting" = Relationship(
        back_populates="quality_control_functions"
    )
    quality_control_function_arguments: list[QualityControlFunctionArgument] = (
        Relationship(back_populates="quality_control_function", cascade_delete=True)
    )


class QualityControlSettingBase(SQLModel):
    permission_group_id: int = Field(foreign_key="permission_group.id")
    name: str
    description: str | None = None
    context_window: str
    is_active: bool = Field(default=False, nullable=True)


class QualityControlSettingCreate(QualityControlSettingBase):
    quality_control_functions: list[QualityControlFunctionCreate]


class QualityControlSettingUpdate(SQLModel):
    permission_group_id: int | None = None
    name: str | None = None
    description: str | None = None
    context_window: str | None = None
    is_active: bool | None = None
    quality_control_functions: list[QualityControlFunctionUpdate] | None = None


class QualityControlSettingPublic(QualityControlSettingBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int | None = None
    created_by_username: str | None = None
    created_at: datetime | None = None
    quality_control_functions: list[QualityControlFunctionPublic]
    permission_group: "PermissionGroup"


class QualityControlSetting(QualityControlSettingBase, table=True):
    __tablename__ = "quality_control_setting"

    __table_args__ = (
        Index(
            "ix_qcs_name_permission_group",
            func.lower(column("name")),
            column("permission_group_id"),
            unique=True,
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4, unique=True)
    created_by_id: int | None = Field(foreign_key="user.id", nullable=True)
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    quality_control_functions: list[QualityControlFunction] = Relationship(
        back_populates="quality_control_setting", cascade_delete=True
    )
    permission_group: "PermissionGroup" = Relationship(
        back_populates="quality_control_setting"
    )

    user: Optional["User"] = Relationship(back_populates="quality_control_setting")

    @property
    def mqtt_information(self) -> list:
        return [
            self.func_mqtt_information(func) for func in self.quality_control_functions
        ]

    @property
    def created_by_username(self) -> str | None:
        return self.user.username if self.user else None

    @staticmethod
    def func_mqtt_information(func) -> dict:
        kwargs = {}
        datastreams = []
        for arg in func.quality_control_function_arguments:
            if arg.type == "datastream":
                for d in arg.input["value"]:
                    datastreams.append(
                        {
                            "arg_name": arg.name,
                            "alias": d["alias"],
                            "sta_thing_id": d["Thing"]["@iot.id"],
                            "sta_stream_id": d["@iot.id"],
                        }
                    )
            if arg.type == "float":
                kwargs[arg.name] = float(arg.input["value"])
            if arg.type == "int":
                kwargs[arg.name] = int(arg.input["value"])
            if arg.type in {"offset", "enum", "str", "function"}:
                kwargs[arg.name] = str(arg.input["value"])
            if arg.type == "bool":
                kwargs[arg.name] = bool(arg.input["value"])

        return {
            "name": func.name,
            "func_id": func.name,
            "kwargs": kwargs,
            "datastreams": datastreams,
        }
