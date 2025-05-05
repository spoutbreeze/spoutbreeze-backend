from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID


class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    keycloak_id: str


class UserResponse(UserBase):
    id: UUID
    keycloak_id: str
    created_at: Optional[datetime] = None
    is_active: bool

    model_config = {
        "from_attributes": True,
    }
    