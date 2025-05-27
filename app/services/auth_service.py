from fastapi import HTTPException, status
from jose import jwt
from app.config.settings import keycloak_openid, get_settings, keycloak_admin

from app.config.logger_config import logger


class AuthService:
    """
    Service for authentication and authorization operations
    """

    def __init__(self):
        self.settings = get_settings()
        self.keycloak_client_id = self.settings.keycloak_client_id

        raw_key = keycloak_openid.public_key()

        if not raw_key.startswith("-----BEGIN"):
            # Format the public key proparly for PEM format
            self.public_key = (
                f"-----BEGIN PUBLIC KEY-----\n{raw_key}\n-----END PUBLIC KEY-----"
            )
        else:
            self.public_key = raw_key

    def validate_token(self, token: str) -> dict:
        """
        Validate and decode the JWT token

        Args:
            token: The JWT token to validate

        Returns:
            dict: The decoded token payload

        Raises:
            HTTPException: If the token is invalid
        """
        try:
            # Log token validation attempt (first 10 chars only for security)
            logger.info(f"Validating token starting with: {token[:10]}...")

            # Try to decode with python-jose library
            try:
                payload = jwt.decode(
                    token,
                    self.public_key,
                    algorithms=["RS256"],
                    options={
                        "verify_aud": False
                    },  # Disable audience verification completely
                )

                # Verify the token has a username
                username = payload.get("preferred_username")
                if not username:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token: missing username",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                logger.info(f"Token validated successfully for user: {username}")
                return payload

            except Exception as e:
                logger.error(f"Jose JWT decode error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token: {str(e)}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        except HTTPException:
            # Re-raise HTTP exceptions
            raise

        except Exception as e:
            # Catch-all for any other exceptions
            logger.error(f"Unexpected token validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def exchange_token(self, code: str, redirect_uri: str, code_verifier: str) -> dict:
        """
        Exchange authorization code for tokens
        """
        try:

            token = keycloak_openid.token(
                grant_type="authorization_code",
                code=code,
                redirect_uri=redirect_uri,
                code_verifier=code_verifier,
            )
            return token
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh the access token using the refresh token

        Args:
            refresh_token: The refresh token to use

        Returns:
            dict: New tokens including access_token, refresh_token and user_info

        Raises:
            HTTPException: If the refresh token is invalid or expired
        """
        try:
            logger.info(
                f"Attempting to refresh token starting with: {refresh_token[:10]}..."
            )

            token_response = keycloak_openid.refresh_token(refresh_token)

            # Get user info with the new token
            user_info = self.get_user_info(token_response["access_token"])

            return {
                "access_token": token_response["access_token"],
                "expires_in": token_response.get("expires_in", 300),
                "refresh_token": token_response["refresh_token"],
                "token_type": "Bearer",
                "user_info": user_info,
            }
        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
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
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user info",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    # def update_user_profile(self, user_id: str, user_data: dict) -> bool:
    #     """
    #     Update user information in Keycloak
    #     """
    #     try:
    #         # Map the field names to Keycloak's expected format
    #         keycloak_user_data = {}
            
    #         if "first_name" in user_data:
    #             keycloak_user_data["firstName"] = user_data["first_name"]
    #         if "last_name" in user_data:
    #             keycloak_user_data["lastName"] = user_data["last_name"]
    #         if "email" in user_data:
    #             keycloak_user_data["email"] = user_data["email"]
    #         if "username" in user_data:
    #             keycloak_user_data["username"] = user_data["username"]

    #         # Update user with the correctly formatted data
    #         keycloak_admin.update_user(user_id, keycloak_user_data)
    #         logger.info(f"User info updated successfully for user ID: {user_id}")
    #         return True    
    #     except Exception as e:
    #         logger.error(f"Failed to update user info: {str(e)}")
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail=f"Failed to update user info: {str(e)}",
    #             headers={"WWW-Authenticate": "Bearer"},
    #         )

    def logout(self, refresh_token: str) -> None:
        """
        Logout the user by invalidating the refresh token
        """
        try:
            keycloak_openid.logout(refresh_token=refresh_token)
            logger.info("User logged out successfully")
        except Exception as e:
            logger.error(f"Failed to logout: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to logout",
                headers={"WWW-Authenticate": "Bearer"},
            )