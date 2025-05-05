import asyncio

from app.config.chat_manager import chat_manager
from app.config.settings import get_settings
from app.config.logger_config import get_logger

logger = get_logger("Twitch")

class TwitchIRCClient:
    def __init__(self):
        self.settings = get_settings()
        self.server = self.settings.twitch_server
        self.port   = self.settings.twitch_port
        self.nickname= self.settings.twitch_nick
        self.token   = self.settings.twitch_token
        self.channel = f"#{self.settings.twitch_channel}"
        self.reader  = None
        self.writer  = None

    async def connect(self):
        while True:
            try:
                # Open a secure TLS connection in one call
                self.reader, self.writer = await asyncio.open_connection(
                    self.server,
                    self.port,
                    ssl=True
                )

                # Send PASS, NICK, JOIN
                self.writer.write(f"PASS {self.token}\r\n".encode())
                self.writer.write(f"NICK {self.nickname}\r\n".encode())
                self.writer.write(f"JOIN {self.channel}\r\n".encode())
                await self.writer.drain()

                logger.info("[TwitchIRC] Connected, listening for messages…")
                await self.listen()
            except Exception as e:
                logger.info(f"[TwitchIRC] Connection error: {e!r}")
                # back off before retrying
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

twitch_client = TwitchIRCClient()