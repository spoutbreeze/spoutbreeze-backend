from pydantic import BaseModel, Field
from typing import Optional

class TokenRequest(BaseModel):
    """
    Model for token exchange request
    """
    token: str = Field(..., description="Authorization code from Keycloak")
    redirect_uri: str = Field(..., description="Redirect URI used in the authorization request")

class TokenResponse(BaseModel):
    """
    Model for token exchange response
    """
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class User(BaseModel):
    """
    Model for user information
    """
    username: str
    password: str
    email: str
    first_name: str
    last_name: str

class UserInfo(BaseModel):
    preferred_username: str
    email: Optional[str] = None
    full_name: Optional[str] = None