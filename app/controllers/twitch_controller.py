from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.config.database.session import get_db
from app.config.twitch_auth import TwitchAuth
from app.models.twitch.twitch_models import TwitchToken
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["Twitch Authentication"])


@router.get("/twitch/callback")
async def twitch_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle Twitch OAuth callback"""
    if error:
        raise HTTPException(status_code=400, detail=f"Twitch OAuth error: {error}")

    try:
        twitch_auth = TwitchAuth()
        token_data = await twitch_auth.exchange_code_for_token(code)

        # Store token in database
        expires_at = datetime.now() + timedelta(
            seconds=token_data.get("expires_in", 3600)
        )

        # Deactivate old tokens using SQLAlchemy ORM
        stmt = update(TwitchToken).where(TwitchToken.is_active).values(is_active=False)
        await db.execute(stmt)

        # Store new token
        token = TwitchToken(
            access_token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
            is_active=True,
        )
        db.add(token)
        await db.commit()

        return {
            "message": "Successfully authenticated with Twitch and token stored",
            "expires_in": token_data.get("expires_in"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to exchange code: {str(e)}"
        )


@router.get("/twitch/login")
async def twitch_login():
    """Redirect user to Twitch for authorization"""
    twitch_auth = TwitchAuth()
    auth_url = twitch_auth.get_authorization_url()
    return {"authorization_url": auth_url}


# @router.post("/twitch/test-refresh")
# async def test_token_refresh(db: AsyncSession = Depends(get_db)):
#     """Test endpoint to force token refresh"""
#     try:
#         from app.config.twitch_irc import TwitchIRCClient
#         twitch_client = TwitchIRCClient()
#         # Check current token status
#         stmt = select(TwitchToken).where(
#             TwitchToken.is_active == True
#         ).order_by(TwitchToken.created_at.desc())

#         result = await db.execute(stmt)
#         token_record = result.scalars().first()

#         if not token_record:
#             return {"error": "No active token found"}

#         current_time = datetime.now()
#         time_until_expiry = token_record.expires_at - current_time

#         response = {
#             "current_token": token_record.access_token[:20] + "...",
#             "expires_at": token_record.expires_at.isoformat(),
#             "time_until_expiry": str(time_until_expiry),
#             "has_refresh_token": bool(token_record.refresh_token),
#             "refresh_needed": token_record.expires_at <= current_time + timedelta(minutes=5)
#         }

#         # Force refresh test
#         await twitch_client.refresh_token_if_needed()

#         # Check if token was updated
#         await db.refresh(token_record)
#         response["token_after_refresh"] = token_record.access_token[:20] + "..."
#         response["new_expires_at"] = token_record.expires_at.isoformat()
#         response["refresh_performed"] = response["current_token"] != response["token_after_refresh"]

#         return response

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

# @router.post("/twitch/simulate-expiring-token")
# async def simulate_expiring_token(db: AsyncSession = Depends(get_db)):
#     """Simulate a token that's about to expire for testing refresh functionality"""
#     try:
#         # Get current active token
#         stmt = select(TwitchToken).where(
#             TwitchToken.is_active == True
#         ).order_by(TwitchToken.created_at.desc())

#         result = await db.execute(stmt)
#         token_record = result.scalars().first()

#         if not token_record:
#             return {"error": "No active token found"}

#         # Set token to expire in 2 minutes (within the 5-minute refresh window)
#         old_expiry = token_record.expires_at
#         token_record.expires_at = datetime.now() + timedelta(minutes=2)
#         await db.commit()

#         current_time = datetime.now()
#         expires_soon_threshold = current_time + timedelta(minutes=5)
#         will_trigger_refresh = token_record.expires_at <= expires_soon_threshold

#         return {
#             "message": "Token set to expire soon for testing",
#             "old_expiry": old_expiry.isoformat(),
#             "new_expiry": token_record.expires_at.isoformat(),
#             "current_time": current_time.isoformat(),
#             "expires_in_minutes": 2,
#             "will_trigger_refresh": will_trigger_refresh,
#             "refresh_threshold": expires_soon_threshold.isoformat(),
#             "instruction": "Now call /auth/twitch/test-refresh to test the refresh mechanism"
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

# @router.get("/twitch/token-status")
# async def get_token_status(db: AsyncSession = Depends(get_db)):
#     """Get current token status"""
#     try:
#         stmt = select(TwitchToken).where(
#             TwitchToken.is_active == True
#         ).order_by(TwitchToken.created_at.desc())

#         result = await db.execute(stmt)
#         token_record = result.scalars().first()

#         if not token_record:
#             return {"error": "No active token found"}

#         current_time = datetime.now()
#         time_until_expiry = token_record.expires_at - current_time

#         return {
#             "token_preview": token_record.access_token[:20] + "...",
#             "expires_at": token_record.expires_at.isoformat(),
#             "current_time": current_time.isoformat(),
#             "time_until_expiry": str(time_until_expiry),
#             "is_expired": token_record.expires_at <= current_time,
#             "expires_soon": token_record.expires_at <= current_time + timedelta(minutes=5),
#             "has_refresh_token": bool(token_record.refresh_token),
#             "created_at": token_record.created_at.isoformat()
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")
