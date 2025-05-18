from fastapi import APIRouter, Depends, HTTPException, status, Form
from datetime import datetime
from fastapi.security import (
    OAuth2AuthorizationCodeBearer,
    HTTPBearer,
)
from app.services.auth_service import AuthService
from app.models.auth_models import (
    TokenRequest,
    TokenResponse,
    RefreshTokenRequest,
)
from app.config.settings import keycloak_openid, get_settings
from app.config.database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models.user_models import User
from app.controllers.user_controller import get_current_user
from typing import cast

from app.config.logger_config import logger
from pydantic import BaseModel


bearer_scheme = HTTPBearer()
settings = get_settings()

router = APIRouter(prefix="/api", tags=["Authentication"])

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{keycloak_openid.well_known()['authorization_endpoint']}",
    tokenUrl=f"{keycloak_openid.well_known()['token_endpoint']}",
)

auth_service = AuthService()


class ProtectedRouteResponse(BaseModel):
    message: str


@router.get("/protected", response_model=ProtectedRouteResponse)
async def protected_route(current_user: User = Depends(get_current_user)):
    """
    Protected route that requires authentication

    Returns:
        A welcome message with the username
    """
    return {"message": f"Hello, {current_user.username}! This is a protected route."}


@router.post("/token", response_model=TokenResponse)
async def exchange_token(request: TokenRequest, db: AsyncSession = Depends(get_db)):
    """
    Exchange an authorization code for access and refresh tokens

    Args:
        request: The token request containing the authorization code and redirect URI

    Returns:
        Access token, refresh token and other token information
    """
    try:
        token_data = auth_service.exchange_token(
            request.code, request.redirect_uri, request.code_verifier
        )

        # Extract the access token
        access_token = token_data.get("access_token")

        # Get user information
        user_info = auth_service.get_user_info(cast(str, access_token))
        print("User info:", user_info)

        # Check if the user already exists
        keycloak_id = user_info.get("sub")

        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await db.execute(stmt)
        existing_user = result.scalars().first()

        if not existing_user:
            # Create a new user in the database
            new_user = User(
                keycloak_id=str(keycloak_id),
                username=str(user_info.get("preferred_username", "")),
                email=str(user_info.get("email", "")),
                first_name=str(user_info.get("given_name", "")),
                last_name=str(user_info.get("family_name", "")),
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            logger.info(
                f"New user created: {new_user.username}, with keycloak ID: {new_user.keycloak_id}"
            )
        else:
            # Update the existing user information
            setattr(
                existing_user,
                "username",
                str(user_info.get("preferred_username", existing_user.username)),
            )
            setattr(
                existing_user, "email", str(user_info.get("email", existing_user.email))
            )
            setattr(
                existing_user,
                "first_name",
                str(user_info.get("given_name", existing_user.first_name)),
            )
            setattr(
                existing_user,
                "last_name",
                str(user_info.get("family_name", existing_user.last_name)),
            )
            setattr(existing_user, "updated_at", datetime.now())
            await db.commit()
            await db.refresh(existing_user)
            logger.info(
                f"User updated: {existing_user.username}, with keycloak ID: {existing_user.keycloak_id}"
            )

        return {
            "access_token": token_data["access_token"],
            "expires_in": token_data["expires_in"],
            "refresh_token": token_data["refresh_token"],
            "token_type": "Bearer",
            "user_info": user_info,
        }
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this Keycloak ID already exists",
        )
    except Exception as e:
        logger.error(f"Error exchanging token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange token: {str(e)}",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh the access token using the refresh token

    Args:
        request: The refresh token request containing the refresh token

    Returns:
        New access token and refresh token
    """
    return auth_service.refresh_token(request.refresh_token)


# FOR DEVELOPMENT ONLY
@router.post("/dev-token", response_model=TokenResponse)
async def get_dev_token(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Development endpoint to get tokens (ONLY FOR LOCAL TESTING)"""
    try:
        # Only allow in development mode
        env = settings.env
        if env != "development":
            raise HTTPException(status_code=404, detail="Not found")

        # Get token from Keycloak
        token_response = keycloak_openid.token(
            grant_type="password", username=username, password=password
        )

        # Process user info
        access_token = token_response.get("access_token")
        user_info = auth_service.get_user_info(cast(str, access_token))

        # Check if user exists
        keycloak_id = user_info.get("sub")
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await db.execute(stmt)
        existing_user = result.scalars().first()

        # Create user if doesn't exist (similar to exchange_token)
        if not existing_user:
            # Create new user logic here
            pass

        # Update the expiration time to 5 hours and 24h for refresh token
        # token_response["expires_in"] = 18000  # 5 hours
        # token_response["refresh_expires_in"] = 86400  # 24 hours
        return {
            "access_token": token_response["access_token"],
            "expires_in": token_response["expires_in"],
            "refresh_token": token_response["refresh_token"],
            "refresh_expires_in": token_response["refresh_expires_in"],
            "token_type": "Bearer",
            "user_info": user_info,
        }

    except Exception as e:
        logger.error(f"Dev token error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to get token: {str(e)}")
