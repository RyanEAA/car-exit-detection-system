from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=80)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserLogin(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_admin: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class DetectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    image_path: str
    original_filename: str | None = None
    media_type: str
    is_car: bool
    view: str | None = None
    license_plate: str | None = None
    exit_date: date
    exit_time: time
    captured_at: datetime


class DetectionRecordResponse(BaseModel):
    detection: DetectionRead
    image_url: str
    media_type: str


class DetectionUpdateRequest(BaseModel):
    license_plate: str | None = Field(default=None, max_length=64)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class HistoryResponse(BaseModel):
    items: list[DetectionRecordResponse]