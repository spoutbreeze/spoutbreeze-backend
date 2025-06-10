import httpx
from app.config.settings import get_settings
from urllib.parse import urlencode
import secrets

settings = get_settings()


class TwitchAuth:
    def __init__(self):
        self.client_id = settings.twitch_client_id
        self.client_secret = settings.twitch_client_secret
        self.redirect_uri = settings.twitch_redirect_uri

    def get_authorization_url(self) -> str:
        """Generate the URL for user authorization"""
        state = secrets.token_urlsafe(32)  # Store this securely
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "chat:read chat:edit",
            "state": state,
        }
        return f"https://id.twitch.tv/oauth2/authorize?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://id.twitch.tv/oauth2/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                },
            )
            response.raise_for_status()
            return response.json()


# Keep the old function for backward compatibility but mark it as deprecated
async def fetch_twitch_token():
    """This generates app tokens which won't work for IRC chat"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            settings.twitch_token_url,
            data={
                "client_id": settings.twitch_client_id,
                "client_secret": settings.twitch_client_secret,
                "grant_type": "client_credentials",
                "scope": "chat:read chat:edit",
            },
        )
        response.raise_for_status()
        token_data = response.json()
        return token_data["access_token"]
