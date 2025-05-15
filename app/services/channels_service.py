from app.models.channel.channels_model import Channel
from app.models.channel.channels_schemas import ChannelCreate
from uuid import UUID
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.config.logger_config import logger


class ChannelsService:
    """
    Service class for managing channels.
    """

    async def create_channel(
        self,
        db: AsyncSession,
        channel_create: ChannelCreate,
        user_id: UUID,
    ) -> Channel:
        """
        Create a new channel.
        """
        try:
            new_channel = Channel(
                name=channel_create.name,
                creator_id=user_id,
            )
            db.add(new_channel)
            await db.commit()
            await db.refresh(new_channel)
            logger.info(f"Channel {new_channel.name} created for user {user_id}")
            return new_channel
        except Exception as e:
            logger.error(f"Error creating channel: {e}")
            await db.rollback()
            raise

    async def get_channels_by_user_id(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> List[Channel]:
        """
        Get all channels for a user.
        """
        try:
            result = await db.execute(
                select(Channel).where(Channel.creator_id == user_id)
            )
            channels = result.scalars().all()
            logger.info(f"Retrieved {len(channels)} channels for user {user_id}")
            return channels
        except Exception as e:
            logger.error(f"Error retrieving channels for user {user_id}: {e}")
            raise

    async def get_channel_by_id(
        self,
        db: AsyncSession,
        channel_id: UUID,
    ) -> Optional[Channel]:
        """
        Get a channel by its ID.
        """
        try:
            result = await db.execute(select(Channel).where(Channel.id == channel_id))
            channel = result.scalar_one_or_none()
            if channel:
                logger.info(f"Retrieved channel {channel.name} with ID {channel_id}")
            else:
                logger.warning(f"Channel with ID {channel_id} not found")
            return channel
        except Exception as e:
            logger.error(f"Error retrieving channel with ID {channel_id}: {e}")
            raise

    async def get_channels(
        self,
        db: AsyncSession,
    ) -> List[Channel]:
        """
        Get all channels.
        """
        try:
            result = await db.execute(select(Channel))
            channels = result.scalars().all()
            logger.info(f"Retrieved {len(channels)} channels")
            return channels
        except Exception as e:
            logger.error(f"Error retrieving channels: {e}")
            raise

    async def get_channel_by_name(
        self,
        db: AsyncSession,
        channel_name: str,
        user_id: UUID,
    ) -> Optional[Channel]:
        """
        Get a channel by its name.
        """
        try:
            result = await db.execute(
                select(Channel).where(
                    Channel.name == channel_name,
                    Channel.creator_id == user_id,
                )
            )
            channel = result.scalar_one_or_none()
            if channel:
                logger.info(f"Retrieved channel {channel.name} for user {user_id}")
            else:
                logger.warning(
                    f"Channel with name {channel_name} not found for user {user_id}"
                )
            return channel
        except Exception as e:
            logger.error(f"Error retrieving channel with name {channel_name}: {e}")
            raise

    async def update_channel(
        self,
        db: AsyncSession,
        channel_id: UUID,
        channel_update: ChannelCreate,
        user_id: UUID,
    ) -> Optional[Channel]:
        """
        Update a channel by ID.
        """
        #  Check if the channel exists and belongs to the user
        stmt = select(Channel).where(
            Channel.id == channel_id,
            Channel.creator_id == user_id,
        )
        result = await db.execute(stmt)
        channel = result.scalar_one_or_none()
        if not channel:
            logger.warning(
                f"Channel with ID {channel_id} not found or does not belong to user {user_id}"
            )
            return None
        try:
            update_data = {
                k: v for k, v in channel_update.model_dump().items() if v is not None
            }
            stmt = update(Channel).where(Channel.id == channel_id).values(**update_data)
            await db.execute(stmt)
            await db.commit()
            await db.refresh(channel)
            logger.info(f"Channel {channel.name} updated for user {user_id}")
            return channel
        except Exception as e:
            logger.error(f"Error updating channel with ID {channel_id}: {e}")
            await db.rollback()
            raise

    async def delete_channel(
        self,
        db: AsyncSession,
        channel_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete a channel by ID.
        """
        # Check if the channel exists and belongs to the user
        stmt = select(Channel).where(
            Channel.id == channel_id,
            Channel.creator_id == user_id,
        )
        result = await db.execute(stmt)
        channel = result.scalar_one_or_none()
        if not channel:
            logger.warning(
                f"Channel with ID {channel_id} not found or does not belong to user {user_id}"
            )
            return False
        try:
            stmt = delete(Channel).where(Channel.id == channel_id)
            await db.execute(stmt)
            await db.commit()
            logger.info(f"Channel {channel.name} deleted for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting channel with ID {channel_id}: {e}")
            await db.rollback()
            raise

    async def get_or_create_channel(
        self,
        db: AsyncSession,
        name: str,
        user_id: UUID,
    ) -> Channel:
        """
        Get or create a channel.
        """
        try:
            stmt = select(Channel).where(
                Channel.name == name,
                Channel.creator_id == user_id,
            )
            result = await db.execute(stmt)
            channel = result.scalar_one_or_none()
            if channel:
                logger.info(f"Channel {channel.name} already exists for user {user_id}")
                return channel
            else:
                channel_create = ChannelCreate(name=name)
                result = await self.create_channel(db, channel_create, user_id)
                logger.info(f"Channel {name} created for user {user_id}")
                return result
        except Exception as e:
            logger.error(
                f"Error getting or creating channel {name} for user {user_id}: {e}"
            )
            raise
