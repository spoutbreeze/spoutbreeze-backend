from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import List, Optional
from datetime import datetime
from fastapi.security import (
    OAuth2AuthorizationCodeBearer,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from app.services.auth_service import AuthService
from app.models.auth_models import (
    TokenRequest,
    TokenResponse,
    UserInfo,
    RefreshTokenRequest,
)
from app.config.settings import keycloak_openid
from app.config.database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.config.database.models import User
from app.config.database.schemas import UserResponse

from app.config.logger_config import logger


bearer_scheme = HTTPBearer()

router = APIRouter(prefix="/api", tags=["Authentication"])

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{keycloak_openid.well_known()['authorization_endpoint']}",
    tokenUrl=f"{keycloak_openid.well_known()['token_endpoint']}",
)

auth_service = AuthService()


async def get_current_user(
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    """
    Dependency to get the current user from the token

    Args:
        authorization: The authorization header containing the Bearer token
        db: The database session

    Returns:
        The current user information
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    token = authorization.split(" ")[1]

    try:
        # Verify and decode token
        token_date = auth_service.validate_token(token)
        keycloak_id = token_date.get("sub")
        if not keycloak_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        # Check if user exists in the database
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the current user information

    Args:
        current_user: The current user information

    Returns:
        The current user information
    """
    return current_user


@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a list of users

    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        db: The database session
        current_user: The current user information

    Returns:
        A list of users
    """
    stmt = select(User).offset(skip).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users


@router.get("/protected", response_model=UserInfo)
async def protected_route(current_user: UserInfo = Depends(get_current_user)):
    """
    Protected route that requires authentication

    Returns:
        A welcome message with the username
    """
    return {
        "message": f"Hello, {current_user.get('preferred_username')}! This is a protected route."
    }


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
        token_data = auth_service.exchange_token(request.code, request.redirect_uri)

        # Extract the access token
        access_token = token_data.get("access_token")

        # Get user information
        user_info = auth_service.get_user_info(access_token)
        print("User info:", user_info)

        # Check if the user already exists
        keycloak_id = user_info.get("sub")
        
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await db.execute(stmt)
        existing_user = result.scalars().first()

        if not existing_user:
            # Create a new user in the database
            new_user = User(
                keycloak_id=keycloak_id,
                username=user_info.get("preferred_username"),
                email=user_info.get("email"),
                first_name=user_info.get("given_name"),
                last_name=user_info.get("family_name"),
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            logger.info(
                f"New user created: {new_user.username}, with keycloak ID: {new_user.keycloak_id}"
            )
        else:
            # Update the existing user information
            existing_user.username = user_info.get("preferred_username")
            existing_user.email = user_info.get("email")
            existing_user.first_name = user_info.get("given_name")
            existing_user.last_name = user_info.get("family_name")
            existing_user.updated_at = datetime.now()
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
