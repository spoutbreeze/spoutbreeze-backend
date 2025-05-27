from fastapi import APIRouter, Depends, HTTPException, status, Header, Path
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.auth_service import AuthService
from app.config.database.session import get_db
from app.config.logger_config import logger
from app.models.user_models import User
from app.models.user_schemas import UserResponse, UpdateProfileRequest


auth_service = AuthService()

router = APIRouter(prefix="/api", tags=["Users"])


async def get_current_user(
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
) -> User:
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

# @router.put("/me/profile", response_model=UserResponse)
# async def update_user_profile(
#     update_data: UpdateProfileRequest,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """
#     Update the current user's profile information
#     Args:
#         update_data: The data to update the user's profile
#         current_user: The current user information
#         db: The database session
#     Returns:
#         The updated user information
#     """
#     try:
#         profile_update_data = {}

#         if update_data.email is not None:
#             profile_update_data["email"] = update_data.email
#         if update_data.first_name is not None:
#             profile_update_data["first_name"] = update_data.first_name
#         if update_data.last_name is not None:
#             profile_update_data["last_name"] = update_data.last_name
#         if not profile_update_data:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="No profile data provided to update",
#             )
#         # Update user in the database
#         if profile_update_data:
#             auth_service.update_user_profile(user_id=current_user.keycloak_id, user_data=profile_update_data)

#             await db.commit()
#             await db.refresh(current_user)
#         logger.info(f"User profile updated: {current_user.username}")
#         return current_user
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         logger.error(f"Error updating user profile: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to update user profile",
#         )


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


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID = Path(..., title="The ID of the user to get"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a user by ID

    Args:
        user_id: The ID of the user to get
        db: The database session
        current_user: The current user information

    Returns:
        The requested user information
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    return user
