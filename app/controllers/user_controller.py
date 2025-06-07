from fastapi import APIRouter, Depends, HTTPException, status, Request, Path
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.auth_service import AuthService
from app.config.database.session import get_db
from app.models.user_models import User
from app.models.user_schemas import UserResponse, UpdateProfileRequest
from app.config.logger_config import logger
from app.config.settings import get_settings
import uuid


auth_service = AuthService()
settings = get_settings()

router = APIRouter(prefix="/api", tags=["Users"])


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from HTTP-only cookie
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Get access token from cookie instead of Authorization header
        access_token = request.cookies.get("access_token")

        if not access_token:
            raise credentials_exception

        # Validate token and get payload
        payload = auth_service.validate_token(access_token)

        # Extract user identifier from token
        keycloak_id = payload.get("sub")
        if keycloak_id is None:
            raise credentials_exception

        # Get user from database
        stmt = select(User).where(User.keycloak_id == keycloak_id)
        result = await db.execute(stmt)
        user = result.scalars().first()

        if user is None:
            raise credentials_exception

        # Store the token payload in the user object for role extraction
        # This is a temporary attribute, not persisted to database
        user._token_payload = payload

        return user

    except HTTPException:
        raise credentials_exception
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Authentication error: {str(e)}")
        raise credentials_exception


def get_current_user_roles(current_user: User = Depends(get_current_user)) -> List[str]:
    """
    Extract client roles from the current user's token payload
    """
    # Get the token payload that was stored in get_current_user
    payload = getattr(current_user, '_token_payload', {})
    
    # Extract roles from resource_access for client roles
    resource_access = payload.get("resource_access", {})
    client_access = resource_access.get(settings.keycloak_client_id, {})
    roles = client_access.get("roles", [])
    
    logger.info(f"User {current_user.username} roles: {roles}")
    return roles


def require_role(required_role: str):
    """
    Create a dependency that checks for a specific client role
    """
    def role_checker(roles: List[str] = Depends(get_current_user_roles)):
        if required_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Role '{required_role}' required to access this resource"
            )
        return True
    return role_checker


def require_any_role(*required_roles: str):
    """
    Create a dependency that checks for any of the specified client roles
    """
    def role_checker(roles: List[str] = Depends(get_current_user_roles)):
        if not any(role in roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"One of these roles required: {', '.join(required_roles)}"
            )
        return True
    return role_checker


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


@router.put("/me/profile", response_model=UserResponse)
async def update_user_profile(
    update_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the current user's profile information
    """
    request_id = str(uuid.uuid4())
    logger.info(
        f"[{request_id}] Starting profile update for user: {current_user.username}"
    )

    try:
        profile_update_data = {}

        if update_data.email is not None:
            profile_update_data["email"] = update_data.email.strip().lower()
            profile_update_data["username"] = update_data.email.strip().lower()
        if update_data.first_name is not None:
            profile_update_data["first_name"] = update_data.first_name.strip()
        if update_data.last_name is not None:
            profile_update_data["last_name"] = update_data.last_name.strip()

        if not profile_update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No profile data provided to update",
            )

        logger.info(
            f"[{request_id}] Updating Keycloak profile for user: {current_user.keycloak_id}"
        )

        # Update user in Keycloak first
        auth_service.update_user_profile(
            user_id=current_user.keycloak_id, user_data=profile_update_data
        )

        logger.info(
            f"[{request_id}] Updating database profile for user: {current_user.username}"
        )

        # Update user in the database
        for field, value in profile_update_data.items():
            setattr(current_user, field, value)

        await db.commit()
        await db.refresh(current_user)

        logger.info(
            f"[{request_id}] Profile update completed successfully for user: {current_user.username}"
        )
        return current_user
    except HTTPException as e:
        await db.rollback()
        logger.error(f"[{request_id}] HTTP error during profile update: {str(e)}")
        raise e
    except Exception as e:
        await db.rollback()
        logger.error(f"[{request_id}] Unexpected error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile",
        )


@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_role("admin")),
):
    """
    Get a list of users (Admin only)

    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        db: The database session
        current_user: The current user information

    Returns:
        A list of users
    """
    logger.info(f"Admin user {current_user.username} is requesting users list")
    stmt = select(User).offset(skip).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID = Path(..., title="The ID of the user to get"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_any_role("admin", "moderator")),
):
    """
    Get a user by ID (Admin only)

    Args:
        user_id: The ID of the user to get
        db: The database session
        current_user: The current user information

    Returns:
        The requested user information
    """
    logger.info(f"User {current_user.username} is requesting user {user_id}")
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    return user
