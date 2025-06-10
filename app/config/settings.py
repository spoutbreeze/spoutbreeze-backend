from pydantic_settings import BaseSettings
from functools import lru_cache
from keycloak import KeycloakOpenID, KeycloakAdmin
import os
import urllib3


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
    plugin_manifests_url: str

    # Broadcaster service settings
    broadcaster_api_url: str

    # Twitch IRC settings
    twitch_server: str
    twitch_port: int
    twitch_nick: str
    twitch_channel: str

    # Twitch OAuth credentials flow settings
    twitch_redirect_uri: str
    twitch_client_id: str
    twitch_client_secret: str
    twitch_token_url: str
    # twitch_user_access_token: str

    # Database settings
    db_url: str

    # Environment settings
    env: str = "development"
    
    # SSL settings
    ssl_cert_file: str = "certs/keycloak.crt"
    ssl_verify: bool = True

    # Api base url
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")

    # Admin credentials for Keycloak
    keycloak_admin_username: str = "admin_firas"  # Add default or use env
    keycloak_admin_password: str = "admin"  # Add default or use env

    model_config = {"env_file": ".env"}


@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

if settings.env == "development" and os.path.exists(settings.ssl_cert_file):
    # Use custom certificate for development with proper SSL
    verify_ssl = settings.ssl_cert_file
elif settings.env == "production":
    # Use system CA bundle for production
    verify_ssl = True
else:
    # Fallback to no verification for local development
    verify_ssl = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Keycloak configuration
keycloak_openid = KeycloakOpenID(
    server_url=get_settings().keycloak_server_url,
    client_id=get_settings().keycloak_client_id,
    realm_name=get_settings().keycloak_realm,
    client_secret_key=get_settings().keycloak_client_secret,
    # verify=verify_ssl,
    verify=False,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


keycloak_admin = KeycloakAdmin(
    server_url=get_settings().keycloak_server_url,
    realm_name=get_settings().keycloak_realm,
    client_id=get_settings().keycloak_client_id,
    client_secret_key=get_settings().keycloak_client_secret,
    # verify=verify_ssl,
    verify=False,
)

# Get OIDC config
# oidc_config = keycloak_openid.well_know()
# jwks_uri = oidc_config["jwks_uri"]
