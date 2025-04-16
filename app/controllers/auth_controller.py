from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from app.services.auth_service import AuthService
from app.models.auth_models import TokenRequest, TokenResponse, UserInfo
from app.config import keycloak_openid

router = APIRouter(prefix="/api", tags=["Authentication"])

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{keycloak_openid.well_known()['authorization_endpoint']}",
    tokenUrl=f"{keycloak_openid.well_known()['token_endpoint']}",
)

auth_service = AuthService()

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency to get the current authenticated user
    """
    return auth_service.validate_token(token)


@router.get("/protected", response_model=UserInfo)
async def protected_route(current_user: UserInfo = Depends(get_current_user)):
    """
    Protected route that requires authentication

    Returns:
        A welcome message with the username
    """
    return {"message": f"Hello, {current_user.get('preferred_username')}! This is a protected route."}


@router.post("/token", response_model=TokenResponse)
async def exchange_token(request: TokenRequest):
    """
    Exchange an authorization code for access and refresh tokens

    Args:
        request: The token request containing the authorization code and redirect URI

    Returns:
        Access token, refresh token and other token information
    """
    return auth_service.exchange_token(request.token, request.redirect_uri)