from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.controllers.auth_controller import router as auth_router
from app.controllers.bbb_controller import router as bbb_router
from app.controllers.broadcaster_controller import router as broadcaster_router

from app.config.chat_manager import chat_manager
from app.config.twitch_irc import twitch_client
import asyncio

app = FastAPI(
    title="SpoutBreeze API",
    description="API for SpoutBreeze application with Keycloak integration",
    version="0.1.0",
)

origins = [
    "http://localhost:3000",
    "https://bbb3.riadvice.ovh"
]
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(broadcaster_router)
app.include_router(bbb_router)

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint that returns a welcome message
    """
    return {"message": "Welcome to SpoutBreeze API"}

@app.on_event("startup")
async def startup_event():
    """
    Schedule the Twitch IRC client to run in the background
    """
    asyncio.create_task(twitch_client.connect())
    print("[TwitchIRC] Scheduled background connect task")

@app.websocket("/ws/chat/")
async def chat_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for chat messages
    """
    await chat_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("/twitch"):
                message = data[len("/twitch "):]
                await twitch_client.send_message(message)
                print(f"[TwitchIRC] Sending message: {message}")
            else:
                await chat_manager.broadcast(data)
    except WebSocketDisconnect:
        chat_manager.disconnect(websocket)
        print("[Chat] Client disconnected")

from fastapi import Depends, HTTPException, status, Request
from keycloak.exceptions import KeycloakError
from jose import JWTError
from app.config.config import keycloak_openid
from pydantic import BaseModel


def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = auth_header.split(" ")[1]

    try:
        # Verify and decode token
        keycloak_openid.introspect(token)  # optional strict check
        user_info = keycloak_openid.userinfo(token)
        return user_info
    except (KeycloakError, JWTError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


class RefreshRequest(BaseModel):
    refresh_token: str

@app.post("/auth/refresh")
def refresh_token(data: RefreshRequest):
    try:
        token = keycloak_openid.refresh_token(data.refresh_token)
        return {
            "access_token": token["access_token"],
            "expires_in": token["expires_in"],
            "refresh_token": token["refresh_token"],
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalid or expired")

