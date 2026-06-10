"""Auth request/response schemas."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user_id: str
    role: str
    full_name: str
