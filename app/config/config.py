from dotenv import load_dotenv
import os
from keycloak import KeycloakOpenID, KeycloakAdmin

# Load environment variables from .env file
load_dotenv()

# Environment variables
keycloak_server_url = os.getenv("KEYCLOAK_SERVER_URL")
keycloak_realm = os.getenv("KEYCLOAK_REALM")
keycloak_client_id = os.getenv("KEYCLOAK_CLIENT_ID")
keycloak_client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET")

# Keycloak configuration
keycloak_openid = KeycloakOpenID(
    server_url=keycloak_server_url,
    client_id=keycloak_client_id,
    realm_name=keycloak_realm,
    client_secret_key=keycloak_client_secret,
)

keycloak_admin = KeycloakAdmin(
    server_url=keycloak_server_url,
    realm_name=keycloak_realm,
    client_id=keycloak_client_id,
    client_secret_key=keycloak_client_secret,
)


# Get OIDC config
# oidc_config = keycloak_openid.well_know()
# jwks_uri = oidc_config["jwks_uri"]