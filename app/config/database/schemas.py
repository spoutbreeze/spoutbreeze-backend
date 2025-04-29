from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    keycloak_id: str


class UserResponse(UserBase):
    id: int
    keycloak_id: str
    created_at: datetime
    is_active: bool

    class Config:
        orm_mode = True