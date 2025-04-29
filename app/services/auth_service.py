from fastapi import HTTPException, status
from jose import jwt
from app.config.settings import keycloak_openid, keycloak_admin, get_settings
from app.models.auth_models import RefreshTokenRequest
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """
    Service for authentication and authorization operations
    """

    def __init__(self):
        self.settings = get_settings()
        self.keycloak_client_id = self.settings.keycloak_client_id
        self.public_key = keycloak_openid.public_key()

    def validate_token(self, token: str) -> dict:
        """
        Validate and decode the JWT token
        """
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"],
                audience=self.keycloak_client_id,
                options={"verify_aud": True},
            )

            username = payload.get("preferred_username")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return payload

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def exchange_token(self, code: str, redirect_uri: str) -> dict:
        """
        Exchange authorization code for tokens
        """
        try:
            token = keycloak_openid.token(
                grant_type="authorization_code",
                code=code,
                redirect_uri=redirect_uri,
            )
            return token
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    def refresh_token(self, data: RefreshTokenRequest) -> dict:
        """
        Refresh the access token using the refresh token
        """
        try:
            token = keycloak_openid.refresh_token(data.refresh_token)
            return {
                "access_token": token["access_token"],
                "expires_in": token["expires_in"],
                "refresh_token": token["refresh_token"],
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token invalid or expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def get_user_info(self, access_token: str) -> dict:
        """
        Get user information from Keycloak using the access token
        """
        try:
            user_info = keycloak_openid.userinfo(access_token)
            return user_info
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user info",
                headers={"WWW-Authenticate": "Bearer"},
            )
        