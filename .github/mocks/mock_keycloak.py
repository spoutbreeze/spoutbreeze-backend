"""
This module mocks Keycloak dependencies for testing purposes.
"""
import sys
from unittest.mock import MagicMock


class MockKeycloakOpenID:
    """Mock implementation of KeycloakOpenID for testing."""

    def __init__(self, *args, **kwargs):
        self.server_url = kwargs.get('server_url', 'http://mock-keycloak:8080')
        self.client_id = kwargs.get('client_id', 'test-client')
        self.realm_name = kwargs.get('realm_name', 'test-realm')
        self.client_secret_key = kwargs.get('client_secret_key', 'test-secret')
        self.verify = kwargs.get('verify', True)

    def public_key(self):
        """Return a mock public key."""
        return "mock-public-key"

    def token(self, *args, **kwargs):
        """Return a mock token response."""
        return {
            "access_token": "mock-access-token",
            "refresh_token": "mock-refresh-token",
            "expires_in": 3600,
            "refresh_expires_in": 86400,
            "token_type": "bearer",
            "id_token": "mock-id-token",
            "not-before-policy": 0,
            "session_state": "mock-session-state",
            "scope": "profile email"
        }

    def userinfo(self, token, *args, **kwargs):
        """Return mock user information."""
        return {
            "sub": "mock-user-id",
            "email": "mock@example.com",
            "preferred_username": "mock_user",
            "given_name": "Mock",
            "family_name": "User",
            "name": "Mock User",
            "email_verified": True
        }

    def logout(self, refresh_token):
        """Mock logout function."""
        return True

    def introspect(self, token, *args, **kwargs):
        """Return mock token introspection information."""
        return {
            "active": True,
            "exp": 9999999999,
            "iat": 1600000000,
            "jti": "mock-jti",
            "iss": f"{self.server_url}/auth/realms/{self.realm_name}",
            "sub": "mock-user-id",
            "typ": "Bearer",
            "session_state": "mock-session-state",
            "client_id": self.client_id,
            "username": "mock_user"
        }

    def decode_token(self, token, *args, **kwargs):
        """Return mock decoded token information."""
        return {
            "sub": "mock-user-id",
            "exp": 9999999999,
            "iat": 1600000000,
            "jti": "mock-jti",
            "iss": f"{self.server_url}/auth/realms/{self.realm_name}",
            "aud": self.client_id,
            "typ": "Bearer",
            "azp": self.client_id,
            "session_state": "mock-session-state",
            "acr": "1",
            "realm_access": {
                "roles": ["offline_access", "user"]
            },
            "resource_access": {
                self.client_id: {
                    "roles": ["user"]
                }
            },
            "scope": "profile email",
            "email_verified": True,
            "preferred_username": "mock_user",
            "email": "mock@example.com",
            "given_name": "Mock",
            "family_name": "User"
        }


class MockKeycloakAdmin:
    """Mock implementation of KeycloakAdmin for testing."""

    def __init__(self, *args, **kwargs):
        self.server_url = kwargs.get('server_url', 'http://mock-keycloak:8080')
        self.realm_name = kwargs.get('realm_name', 'test-realm')
        self.user_realm_name = kwargs.get('user_realm_name', 'test-realm')
        self.client_id = kwargs.get('client_id', 'admin-cli')
        self.client_secret_key = kwargs.get('client_secret_key', '')
        self.username = kwargs.get('username', '')
        self.password = kwargs.get('password', '')
        self.verify = kwargs.get('verify', True)
        self.token = {'access_token': 'mock-admin-token'}

    def get_users(self, *args, **kwargs):
        """Return a list of mock users."""
        query = kwargs.get('query', '')
        if query:
            username = query.get('username', '')
            if username:
                return [{"id": f"mock-user-id-{username}", "username": username}]

        return [
            {"id": "mock-user-id-1", "username": "mock_user1"},
            {"id": "mock-user-id-2", "username": "mock_user2"}
        ]

    def get_user_id(self, username, *args, **kwargs):
        """Return a mock user ID for the given username."""
        return f"mock-user-id-{username}"

    def get_user(self, user_id, *args, **kwargs):
        """Return mock user details for the given user ID."""
        username = user_id.replace("mock-user-id-", "")
        return {
            "id": user_id,
            "createdTimestamp": 1600000000000,
            "username": username,
            "enabled": True,
            "totp": False,
            "emailVerified": True,
            "firstName": "Mock",
            "lastName": f"User {username}",
            "email": f"{username}@example.com",
            "attributes": {},
            "disableableCredentialTypes": [],
            "requiredActions": [],
            "notBefore": 0,
            "access": {
                "manageGroupMembership": True,
                "view": True,
                "mapRoles": True,
                "impersonate": False,
                "manage": True
            }
        }

    def create_user(self, payload, *args, **kwargs):
        """Mock creating a user."""
        return payload.get("id", "new-mock-user-id")

    def delete_user(self, user_id, *args, **kwargs):
        """Mock deleting a user."""
        return True

    def get_realm_roles(self):
        """Return mock realm roles."""
        return [
            {"id": "mock-role-id-1", "name": "user"},
            {"id": "mock-role-id-2", "name": "admin"}
        ]

    def get_user_realm_roles(self, user_id):
        """Return mock realm roles for a user."""
        return [
            {"id": "mock-role-id-1", "name": "user"}
        ]

    def assign_realm_roles(self, user_id, roles):
        """Mock assigning realm roles to a user."""
        return True


# Create mock exceptions
class KeycloakError(Exception):
    """Base Keycloak exception."""

    def __init__(self, error_message="", response_code=400, response_body=""):
        self.response_code = response_code
        self.response_body = response_body
        self.error_message = error_message
        super().__init__(error_message)


class KeycloakGetError(KeycloakError):
    """Keycloak GET operation error."""
    pass


class KeycloakPostError(KeycloakError):
    """Keycloak POST operation error."""
    pass


class KeycloakPutError(KeycloakError):
    """Keycloak PUT operation error."""
    pass


class KeycloakDeleteError(KeycloakError):
    """Keycloak DELETE operation error."""
    pass


class KeycloakAuthenticationError(KeycloakError):
    """Keycloak authentication error."""
    pass


class KeycloakConnectionError(KeycloakError):
    """Keycloak connection error."""
    pass


# Create the module structure
keycloak = MagicMock()
keycloak.KeycloakOpenID = MockKeycloakOpenID
keycloak.KeycloakAdmin = MockKeycloakAdmin

# Add exceptions to the module
keycloak.exceptions = MagicMock()
keycloak.exceptions.KeycloakError = KeycloakError
keycloak.exceptions.KeycloakGetError = KeycloakGetError
keycloak.exceptions.KeycloakPostError = KeycloakPostError
keycloak.exceptions.KeycloakPutError = KeycloakPutError
keycloak.exceptions.KeycloakDeleteError = KeycloakDeleteError
keycloak.exceptions.KeycloakAuthenticationError = KeycloakAuthenticationError
keycloak.exceptions.KeycloakConnectionError = KeycloakConnectionError

# Export the module
sys.modules['keycloak'] = keycloak