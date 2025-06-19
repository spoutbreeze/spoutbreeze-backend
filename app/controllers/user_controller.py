from fastapi import APIRouter, Depends, HTTPException, status, Request, Path
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.auth_service import AuthService
from app.config.database.session import get_db
from app.models.user_models import User
from app.models.user_schemas import UserResponse, UpdateProfileRequest, UpdateUserRoleRequest
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
    Get roles from the database (stored from Keycloak)
    """
    user_roles = (
        current_user.get_roles_list()
    )  # Use helper method to convert string to list
    logger.info(f"User {current_user.username} roles: {user_roles}")
    return user_roles


def require_role(required_role: str):
    """
    Create a dependency that checks for a specific role using database roles
    """

    def role_checker(current_user: User = Depends(get_current_user)):
        if not current_user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required to access this resource",
            )
        return True

    return role_checker


def require_any_role(*required_roles: str):
    """
    Create a dependency that checks for any of the specified roles using database roles
    """

    def role_checker(current_user: User = Depends(get_current_user)):
        if not current_user.has_any_role(*required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join(required_roles)}",
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


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    role_data: UpdateUserRoleRequest,
    user_id: UUID = Path(..., title="The ID of the user to update"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_role("admin")),
):
    """
    Update a user's role (Admin only)

    Args:
        user_id: The ID of the user to update
        role_data: The new role data
        db: The database session
        current_user: The current user information

    Returns:
        The updated user information
    """
    request_id = str(uuid.uuid4())
    logger.info(
        f"[{request_id}] Admin {current_user.username} updating role for user {user_id} to {role_data.role}"
    )

    try:
        # Get the target user
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        target_user = result.scalars().first()

        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        # Validate role format
        new_role = role_data.role.strip().lower()
        if not new_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role cannot be empty",
            )

        # Add validation for allowed roles (optional but recommended)
        allowed_roles = ["admin", "moderator"]
        if new_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{new_role}' is not allowed. Allowed roles: {', '.join(allowed_roles)}",
            )

        # Prevent admin from changing their own role (optional security measure)
        if target_user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify your own role",
            )

        logger.info(
            f"[{request_id}] Updating role in Keycloak for user: {target_user.keycloak_id}"
        )

        # Update role in Keycloak first - this will now throw more specific errors
        try:
            auth_service.update_user_role(
                user_id=target_user.keycloak_id, 
                new_role=new_role
            )
        except HTTPException as e:
            # Re-raise HTTP exceptions from auth_service with better context
            logger.error(f"[{request_id}] Keycloak role update failed: {e.detail}")
            raise HTTPException(
                status_code=e.status_code,
                detail=f"Failed to update role in Keycloak: {e.detail}",
            )

        logger.info(
            f"[{request_id}] Updating role in database for user: {target_user.username}"
        )

        # Update role in the database
        target_user.roles = new_role

        await db.commit()
        await db.refresh(target_user)

        logger.info(
            f"[{request_id}] Role update completed successfully for user: {target_user.username}"
        )
        return target_user

    except HTTPException as e:
        await db.rollback()
        logger.error(f"[{request_id}] HTTP error during role update: {str(e)}")
        raise e
    except Exception as e:
        await db.rollback()
        logger.error(f"[{request_id}] Unexpected error updating user role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role",
        )
