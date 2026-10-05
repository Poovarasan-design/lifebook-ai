from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, model_validator
from datetime import datetime
import re

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None
    auth_provider: str = "local"
    role: str = "user"
    is_active: bool = True
    preferences: Dict[str, Any] = {}
    created_at: datetime

    @model_validator(mode="after")
    def populate_name(self) -> "UserOut":
        if not self.name:
            self.name = self.full_name
        return self

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None

class UserRegister(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    email: EmailStr
    password: str
    confirm_password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"[0-9!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one number or special character")
        return v

    @model_validator(mode="after")
    def validate_matching_passwords_and_name(self):
        # Resolve full_name from name or full_name
        resolved_name = self.full_name or self.name
        if not resolved_name or not resolved_name.strip():
            raise ValueError("Name is required")
        self.full_name = resolved_name.strip()
        self.name = self.full_name

        # Validate confirm_password if present
        if self.confirm_password is not None and self.confirm_password != self.password:
            raise ValueError("Passwords do not match")
        return self

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    id_token: Optional[str] = None
    code: Optional[str] = None
    redirect_uri: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class ChangePassword(BaseModel):
    current_password: str
    new_password: str
