import os
import socket
import ssl
import asyncio
from pyexpat.errors import messages

from dotenv import load_dotenv
from app.config.chat_manager import chat_manager

load_dotenv()

class TwitchIRCClient:
    def __init__(self):
        self.server  = os.getenv("TWITCH_SERVER", "irc.chat.twitch.tv")
        self.port    = int(os.getenv("TWITCH_PORT", 6697))
        self.nickname= os.getenv("TWITCH_NICK")
        self.token   = os.getenv("TWITCH_TOKEN")
        self.channel = f"#{os.getenv('TWITCH_CHANNEL')}"
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

                print("[TwitchIRC] Connected, listening for messages…")
                await self.listen()
            except Exception as e:
                print(f"[TwitchIRC] Connection error: {e!r}")
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
                print(f"[TwitchIRC] ← {msg}")

                # (optional) parse out username and text
                # prefix is like: ":username!username@username.tmi.twitch.tv PRIVMSG #channel :message text"
                try:
                    payload = msg.split("PRIVMSG", 1)[1]
                    user = msg.split("!", 1)[0].lstrip(":")
                    text = payload.split(":", 1)[1]
                    print(f"[TwitchIRC] {user}: {text}")
                except Exception:
                    pass

                await chat_manager.broadcast(msg)

    async def send_message(self, message: str):
        if self.writer:
            full_message = f"PRIVMSG {self.channel} :{message}\r\n"
            self.writer.write(full_message.encode())
            await self.writer.drain()
            print(f"[TwitchIRC] Sent: {message}")
        else:
            print("[TwitchIRC] Writer not initialized, cannot send message.")

twitch_client = TwitchIRCClient()