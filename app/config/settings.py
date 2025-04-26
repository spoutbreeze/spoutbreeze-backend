from pydantic_settings import BaseSettings
from functools import lru_cache
from keycloak import KeycloakOpenID, KeycloakAdmin


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

    # Twitch settings
    twitch_server: str
    twitch_port: int
    twitch_nick: str
    twitch_token: str
    twitch_channel: str

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()

# Keycloak configuration
keycloak_openid = KeycloakOpenID(
    server_url=get_settings().keycloak_server_url,
    client_id=get_settings().keycloak_client_id,
    realm_name=get_settings().keycloak_realm,
    client_secret_key=get_settings().keycloak_client_secret,
)

keycloak_admin = KeycloakAdmin(
    server_url=get_settings().keycloak_server_url,
    realm_name=get_settings().keycloak_realm,
    client_id=get_settings().keycloak_client_id,
    client_secret_key=get_settings().keycloak_client_secret,
)

# Get OIDC config
# oidc_config = keycloak_openid.well_know()
# jwks_uri = oidc_config["jwks_uri"]