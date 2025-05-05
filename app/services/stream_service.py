from app.models.stream_models import StreamSettings
from app.models.stream_schemas import (
    StreamSettingsResponse,
    StreamSettingsListResponse,
    StreamSettingsUpdate,
    CreateStreamSettingsCreate,
    StreamSettingsDeleteResponse,
)
from uuid import UUID
from typing import List, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.config.logger_config import logger


class StreamService:
    """
    Service for creating the stream settings
    """

    async def create_stream_settings(
        self,
        stream_settings: CreateStreamSettingsCreate,
        user_id: UUID,
        db: AsyncSession,
    ) -> StreamSettingsResponse:
        """
        Create a stream settings for a user
        """
        new_stream_settings = StreamSettings(
            title=stream_settings.title,
            stream_key=stream_settings.stream_key,
            rtmp_url=stream_settings.rtmp_url,
            user_id=user_id,
        )
        db.add(new_stream_settings)
        await db.commit()
        await db.refresh(new_stream_settings)

        logger.info(
            f"Stream settings with the name {new_stream_settings.title} created for user {user_id}"
        )
        return new_stream_settings

    async def get_stream_settings_by_user_id(
        self,
        user_id: UUID,
        db: AsyncSession,
    ) -> StreamSettingsListResponse:
        """
        Get all stream settings for a user
        """
        stmt = select(StreamSettings).where(StreamSettings.user_id == user_id)
        result = await db.execute(stmt)
        stream_settings = result.scalars().all()

        logger.info(f"Stream settings retrieved for user {user_id}")
        return list(stream_settings)

    async def get_stream_settings_by_id(
        self,
        stream_settings_id: UUID,
        db: AsyncSession,
    ) -> StreamSettingsResponse:
        """
        Get stream settings by ID
        """
        stmt = select(StreamSettings).where(StreamSettings.id == stream_settings_id)
        result = await db.execute(stmt)
        stream_settings = result.scalars().first()

        logger.info(f"Stream settings retrieved with ID {stream_settings_id}")
        return stream_settings

    async def update_stream_settings(
        self,
        stream_settings_id: UUID,
        stream_settings_update: StreamSettingsUpdate,
        db: AsyncSession,
    ) -> StreamSettingsResponse:
        """
        Update stream settings by ID
        """
        # Check if the stream settings exist
        select_stmt = select(StreamSettings).where(StreamSettings.id == stream_settings_id)
        result = await db.execute(select_stmt)
        stream_settings = result.scalars().first()
        if not stream_settings:
            logger.warning(f"Stream settings with ID {stream_settings_id} not found")
            return None
        
        # Update the stream settings
        update_stmt = (
            update(StreamSettings)
            .where(StreamSettings.id == stream_settings_id)
            .values(
                title=stream_settings_update.title,
                rtmp_url=stream_settings_update.rtmp_url,
                stream_key=stream_settings_update.stream_key,
            )
        )
        await db.execute(update_stmt)
        await db.commit()
        await db.refresh(stream_settings)
        logger.info(
            f"Stream settings with ID {stream_settings_id} updated for user {stream_settings.user_id}"
        )
        return stream_settings
    
    async def delete_stream_settings(
        self,
        stream_settings_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> StreamSettingsDeleteResponse:
        """
        Delete stream settings by ID
        """
        # Check if the stream settings exist
        select_stmt = select(StreamSettings).where(
            StreamSettings.id == stream_settings_id,
            StreamSettings.user_id == user_id,
        )
        result = await db.execute(select_stmt)
        stream_settings = result.scalars().first()
        if not stream_settings:
            logger.warning(f"Stream settings with ID {stream_settings_id} not found")
            return None

        # Delete the stream settings
        delete_stmt = delete(StreamSettings).where(StreamSettings.id == stream_settings_id)
        await db.execute(delete_stmt)
        await db.commit()
        logger.info(
            f"Stream settings with ID {stream_settings_id} deleted for user {user_id}"
        )
        return StreamSettingsDeleteResponse(
            message="Stream settings deleted successfully",
            id=stream_settings_id,
        )
