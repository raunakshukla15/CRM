from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    entity_type: str | None = None
    entity_id: int | None = None
    description: str
    created_at: datetime


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
    page: int
    page_size: int
