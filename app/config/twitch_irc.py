import asyncio
import httpx
from datetime import datetime, timedelta
from sqlalchemy import select
from fastapi import HTTPException
from typing import Optional, Dict, Any

from app.config.chat_manager import chat_manager
from app.config.settings import get_settings
from app.config.logger_config import get_logger
from app.config.database.session import get_db
from app.models.twitch.twitch_models import TwitchToken

logger = get_logger("Twitch")


class TwitchIRCClient:
    def __init__(self):
        self.settings = get_settings()
        self.server = self.settings.twitch_server
        self.port = self.settings.twitch_port
        self.nickname = self.settings.twitch_nick
        self.channel = f"#{self.settings.twitch_channel}"
        self.reader = None
        self.writer = None
        self.token = None

    async def get_active_token(self) -> str:
        """Get the active token from database"""
        try:
            # Get database session
            async for db in get_db():
                # Query for active, non-expired token
                stmt = (
                    select(TwitchToken)
                    .where(
                        TwitchToken.is_active == True,
                        TwitchToken.expires_at > datetime.now(),
                    )
                    .order_by(TwitchToken.created_at.desc())
                )

                result = await db.execute(stmt)
                token_record = result.scalars().first()

                if token_record:
                    logger.info("[TwitchIRC] Using database user access token")
                    return token_record.access_token
                else:
                    logger.warning("[TwitchIRC] No valid token found in database")
                    raise HTTPException(
                        status_code=401,
                        detail="No valid Twitch token found. Please authenticate via /auth/twitch/login",
                    )

            # This should never be reached due to the logic above, but mypy needs it
            raise HTTPException(
                status_code=500,
                detail="Unexpected error: database session not available",
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[TwitchIRC] Error fetching token from database: {e}")
            raise HTTPException(
                status_code=500, detail="Database error while fetching Twitch token"
            )

    async def refresh_token_if_needed(self):
        """Check if token needs refresh and refresh if possible"""
        try:
            async for db in get_db():
                stmt = (
                    select(TwitchToken)
                    .where(TwitchToken.is_active == True)
                    .order_by(TwitchToken.created_at.desc())
                )

                result = await db.execute(stmt)
                token_record = result.scalars().first()

                if not token_record:
                    logger.warning("[TwitchIRC] No active token found")
                    break

                # Check if token expires within 5 minutes or has already expired
                expires_soon = datetime.now() + timedelta(minutes=5)

                if token_record.expires_at <= expires_soon:
                    logger.info(
                        "[TwitchIRC] Token expires soon or has expired, attempting refresh..."
                    )

                    if token_record.refresh_token:
                        new_token_data = await self._refresh_access_token(
                            token_record.refresh_token
                        )

                        if new_token_data:
                            # Update the existing token record
                            new_expires_at = datetime.now() + timedelta(
                                seconds=new_token_data.get("expires_in", 3600)
                            )

                            token_record.access_token = new_token_data["access_token"]
                            token_record.expires_at = new_expires_at
                            # Refresh token might be updated too
                            if new_token_data.get("refresh_token"):
                                token_record.refresh_token = new_token_data[
                                    "refresh_token"
                                ]

                            await db.commit()
                            logger.info("[TwitchIRC] Token refreshed successfully")

                            # Update the current token if we're using this one
                            if (
                                hasattr(self, "token")
                                and self.token == token_record.access_token
                            ):
                                self.token = new_token_data["access_token"]
                        else:
                            logger.error(
                                "[TwitchIRC] Failed to refresh token, marking as inactive"
                            )
                            token_record.is_active = False
                            await db.commit()
                    else:
                        logger.warning(
                            "[TwitchIRC] No refresh token available, marking as inactive"
                        )
                        token_record.is_active = False
                        await db.commit()
                break
        except Exception as e:
            logger.error(f"[TwitchIRC] Error checking/refreshing token: {e}")

    async def _refresh_access_token(
        self, refresh_token: str
    ) -> Optional[Dict[str, Any]]:
        """Refresh the access token using the refresh token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://id.twitch.tv/oauth2/token",
                    data={
                        "client_id": self.settings.twitch_client_id,
                        "client_secret": self.settings.twitch_client_secret,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code == 200:
                    token_data = response.json()
                    logger.info("[TwitchIRC] Access token refreshed successfully")
                    return token_data
                else:
                    logger.error(
                        f"[TwitchIRC] Token refresh failed: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            logger.error(f"[TwitchIRC] Exception during token refresh: {e}")
            return None

    async def connect(self):
        """Connect to Twitch IRC with database token"""
        while True:
            try:
                # Check and refresh token if needed before connecting
                await self.refresh_token_if_needed()

                # Get fresh token from database
                self.token = await self.get_active_token()

                if not self.token:
                    logger.error(
                        "[TwitchIRC] No token available, retrying in 30 seconds..."
                    )
                    await asyncio.sleep(30)
                    continue

                # logger.info(f"[TwitchIRC] Using token: {self.token[:10]}...")

                # Open a secure TLS connection in one call
                self.reader, self.writer = await asyncio.open_connection(
                    self.server, self.port, ssl=True
                )

                # Send PASS, NICK, JOIN
                self.writer.write(f"PASS oauth:{self.token}\r\n".encode())
                self.writer.write(f"NICK {self.nickname}\r\n".encode())
                self.writer.write(f"JOIN {self.channel}\r\n".encode())
                await self.writer.drain()

                logger.info("[TwitchIRC] Connected, listening for messages…")
                await self.listen()
            except Exception as e:
                logger.info(f"[TwitchIRC] Connection error: {e!r}")
                # Back off before retrying
                await asyncio.sleep(5)

    async def listen(self):
        while True:
            line = await self.reader.readline()
            if not line:
                # socket closed
                raise ConnectionResetError("Stream closed")
            msg = line.decode(errors="ignore").strip()

            if msg.startswith("PING"):
                # respond to PING to keep the connection alive
                self.writer.write("PONG :tmi.twitch.tv\r\n".encode())
                await self.writer.drain()
                continue

            if "PRIVMSG" in msg:
                # raw IRC line
                logger.info(f"[TwitchIRC] ← {msg}")

                # (optional) parse out username and text
                # prefix is like: ":username!username@username.tmi.twitch.tv PRIVMSG #channel :message text"
                try:
                    payload = msg.split("PRIVMSG", 1)[1]
                    user = msg.split("!", 1)[0].lstrip(":")
                    text = payload.split(":", 1)[1]
                    logger.info(f"[TwitchIRC] {user}: {text}")
                except Exception:
                    pass

                await chat_manager.broadcast(msg)

    async def send_message(self, message: str):
        if self.writer:
            full_message = f"PRIVMSG {self.channel} :{message}\r\n"
            self.writer.write(full_message.encode())
            await self.writer.drain()
            logger.info(f"[TwitchIRC] Sent: {message}")
        else:
            logger.info("[TwitchIRC] Writer not initialized, cannot send message.")

    async def start_token_refresh_scheduler(self):
        """Start a background task to periodically check and refresh tokens"""
        while True:
            try:
                await self.refresh_token_if_needed()
                # Check every 30 minutes
                await asyncio.sleep(1800)
            except Exception as e:
                logger.error(f"[TwitchIRC] Token refresh scheduler error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
