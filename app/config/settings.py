from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    # Keycloak settings
    keycloak_server_url: str
    keycloak_client_id: str
    keycloak_client_secret: str
    keycloak_realm: str

    # BBB API settings
    bbb_server_base_url: str
    bbb_secret: str

    # Broadcaster service settings
    broadcaster_api_url: str

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()