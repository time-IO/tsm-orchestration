from sqlmodel import SQLModel, Field, Column, Relationship, UniqueConstraint
import uuid as uuid_pkg
from datetime import datetime, timezone
from sqlalchemy import JSON
from .permission_group import PermissionGroup


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


class QualityControlFunctionCreate(SQLModel):
    name: str
    quality_control_function_arguments: list[QualityControlFunctionArgumentCreate]


class QualityControlFunctionPublic(SQLModel):
    id: int
    name: str
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
    is_active: bool = Field(default=False, nullable=True)


class QualityControlSettingCreate(QualityControlSettingBase):
    quality_control_functions: list[QualityControlFunctionCreate]


class QualityControlSettingPublic(QualityControlSettingBase):
    id: int
    uuid: uuid_pkg.UUID
    created_by_id: int
    created_at: datetime
    quality_control_functions: list[QualityControlFunctionPublic]
    permission_group: "PermissionGroup"


class QualityControlSetting(QualityControlSettingBase, table=True):
    __tablename__ = "quality_control_setting"

    __table_args__ = (
        UniqueConstraint(
            "name", "permission_group_id", name="qcs_unique_name_permission_group"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)
    created_by_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    quality_control_functions: list[QualityControlFunction] = Relationship(
        back_populates="quality_control_setting", cascade_delete=True
    )
    permission_group: "PermissionGroup" = Relationship(
        back_populates="quality_control_setting"
    )
