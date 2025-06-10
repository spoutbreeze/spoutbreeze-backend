from app.models.stream_models import StreamSettings
from app.models.user_models import User
from app.models.stream_schemas import (
    StreamSettingsResponse,
    StreamSettingsUpdate,
    CreateStreamSettingsCreate,
    StreamSettingsDeleteResponse,
)
from uuid import UUID
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.config.logger_config import logger


class RtmpEndpointService:
    """
    Service for creating the stream settings
    """

    def _create_stream_settings_response(
        self, stream_settings: StreamSettings, user: User
    ) -> StreamSettingsResponse:
        """
        Create a StreamSettingsResponse with user information.
        """
        return StreamSettingsResponse(
            id=stream_settings.id,
            title=stream_settings.title,
            stream_key=stream_settings.stream_key,
            rtmp_url=stream_settings.rtmp_url,
            user_id=stream_settings.user_id,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            created_at=stream_settings.created_at,
            updated_at=stream_settings.updated_at,
        )

    async def create_stream_settings(
        self,
        stream_settings: CreateStreamSettingsCreate,
        user_id: UUID,
        db: AsyncSession,
    ) -> StreamSettingsResponse:
        """
        Create a stream settings for a user
        """
        try:
            new_stream_settings = StreamSettings(
                title=stream_settings.title,
                stream_key=stream_settings.stream_key,
                rtmp_url=stream_settings.rtmp_url,
                user_id=user_id,
            )
            db.add(new_stream_settings)
            await db.commit()
            await db.refresh(new_stream_settings)

            # Get the user information
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one()

            logger.info(
                f"Stream settings with the name {new_stream_settings.title} created for user {user_id}"
            )
            return self._create_stream_settings_response(new_stream_settings, user)
        except Exception as e:
            logger.error(f"Error creating stream settings: {e}")
            await db.rollback()
            raise

    async def get_all_stream_settings(
        self,
        db: AsyncSession,
    ) -> List[StreamSettingsResponse]:
        """
        Get all stream settings
        """
        try:
            result = await db.execute(
                select(StreamSettings, User).join(
                    User, StreamSettings.user_id == User.id
                )
            )
            stream_settings_user_pairs = result.all()

            stream_settings_list = [
                self._create_stream_settings_response(stream_settings, user)
                for stream_settings, user in stream_settings_user_pairs
            ]

            logger.info(f"Retrieved {len(stream_settings_list)} stream settings")
            return stream_settings_list
        except Exception as e:
            logger.error(f"Error retrieving stream settings: {str(e)}")
            raise e

    async def get_stream_settings_by_user_id(
        self,
        user_id: UUID,
        db: AsyncSession,
    ) -> List[StreamSettingsResponse]:
        """
        Get all stream settings for a user
        """
        try:
            result = await db.execute(
                select(StreamSettings, User)
                .join(User, StreamSettings.user_id == User.id)
                .where(StreamSettings.user_id == user_id)
            )
            stream_settings_user_pairs = result.all()

            stream_settings_list = [
                self._create_stream_settings_response(stream_settings, user)
                for stream_settings, user in stream_settings_user_pairs
            ]

            logger.info(
                f"Retrieved {len(stream_settings_list)} stream settings for user {user_id}"
            )
            return stream_settings_list
        except Exception as e:
            logger.error(f"Error retrieving stream settings for user {user_id}: {e}")
            raise

    async def get_stream_settings_by_id(
        self,
        stream_settings_id: UUID,
        db: AsyncSession,
    ) -> Optional[StreamSettingsResponse]:
        """
        Get stream settings by ID
        """
        try:
            result = await db.execute(
                select(StreamSettings, User)
                .join(User, StreamSettings.user_id == User.id)
                .where(StreamSettings.id == stream_settings_id)
            )
            stream_settings_user_pair = result.first()

            if stream_settings_user_pair:
                stream_settings, user = stream_settings_user_pair
                logger.info(f"Stream settings retrieved with ID {stream_settings_id}")
                return self._create_stream_settings_response(stream_settings, user)
            else:
                logger.warning(
                    f"Stream settings with ID {stream_settings_id} not found"
                )
                return None
        except Exception as e:
            logger.error(
                f"Error retrieving stream settings with ID {stream_settings_id}: {e}"
            )
            raise

    async def update_stream_settings(
        self,
        stream_settings_id: UUID,
        stream_settings_update: StreamSettingsUpdate,
        db: AsyncSession,
    ) -> Optional[StreamSettingsResponse]:
        """
        Update stream settings by ID
        """
        try:
            # Check if the stream settings exist and get user info
            result = await db.execute(
                select(StreamSettings, User)
                .join(User, StreamSettings.user_id == User.id)
                .where(StreamSettings.id == stream_settings_id)
            )
            stream_settings_user_pair = result.first()

            if not stream_settings_user_pair:
                logger.warning(
                    f"Stream settings with ID {stream_settings_id} not found"
                )
                return None

            stream_settings, user = stream_settings_user_pair

            # Update the stream settings
            update_data = {
                k: v
                for k, v in stream_settings_update.model_dump().items()
                if v is not None
            }

            if update_data:
                update_stmt = (
                    update(StreamSettings)
                    .where(StreamSettings.id == stream_settings_id)
                    .values(**update_data)
                )
                await db.execute(update_stmt)
                await db.commit()
                await db.refresh(stream_settings)

            logger.info(
                f"Stream settings with ID {stream_settings_id} updated for user {stream_settings.user_id}"
            )
            return self._create_stream_settings_response(stream_settings, user)
        except Exception as e:
            logger.error(
                f"Error updating stream settings with ID {stream_settings_id}: {e}"
            )
            await db.rollback()
            raise

    async def delete_stream_settings(
        self,
        stream_settings_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> Optional[StreamSettingsDeleteResponse]:
        """
        Delete stream settings by ID
        """
        try:
            # Check if the stream settings exist
            select_stmt = select(StreamSettings).where(
                StreamSettings.id == stream_settings_id,
                StreamSettings.user_id == user_id,
            )
            result = await db.execute(select_stmt)
            stream_settings = result.scalars().first()
            if not stream_settings:
                logger.warning(
                    f"Stream settings with ID {stream_settings_id} not found"
                )
                return None

            # Delete the stream settings
            delete_stmt = delete(StreamSettings).where(
                StreamSettings.id == stream_settings_id
            )
            await db.execute(delete_stmt)
            await db.commit()
            logger.info(
                f"Stream settings with ID {stream_settings_id} deleted for user {user_id}"
            )
            return StreamSettingsDeleteResponse(
                message="Stream settings deleted successfully",
                id=stream_settings_id,
            )
        except Exception as e:
            logger.error(
                f"Error deleting stream settings with ID {stream_settings_id}: {e}"
            )
            await db.rollback()
            raise
