from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from app.controllers.auth_controller import router as auth_router
from app.controllers.bbb_controller import router as bbb_router
from app.controllers.broadcaster_controller import router as broadcaster_router
from app.controllers.user_controller import router as user_router
from app.controllers.stream_controller import router as stream_router

from app.config.chat_manager import chat_manager
from app.config.twitch_irc import twitch_client
from app.config.logger_config import get_logger
from app.config.settings import get_settings
import asyncio

logger = get_logger("Twitch")
setting = get_settings()

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """
#     Lifespan context manager for the FastAPI application
#     """
#     # Startup: schedule the IRC client
#     task = asyncio.create_task(twitch_client.connect())
#     logger.info("[TwitchIRC] Background connect task scheduled")

#     yield  # your app is running

#     # Shutdown: cancel the IRC task
#     task.cancel()
#     try:
#         await task
#     except asyncio.CancelledError:
#         logger.info("[TwitchIRC] Connect task cancelled cleanly")

app = FastAPI(
    # lifespan=lifespan,
)

# @app.on_event("startup")
# async def startup_event():
#     """
#     Schedule the Twitch IRC client to run in the background
#     """
#     asyncio.create_task(twitch_client.connect())
#     print("[TwitchIRC] Scheduled background connect task")

# Override the default Swagger UI to add OAuth support
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="/favicon.ico",
        init_oauth={
            "clientId": setting.keycloak_client_id,
            "usePkceWithAuthorizationCodeGrant": True,
            "clientSecret": setting.keycloak_client_secret,
            "realm": setting.keycloak_realm,
            "appName": "SpoutBreeze API",
            "scope": "openid profile email",
            "additionalQueryStringParams": {}
        }
    )

# Update OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    # Get the auto-generated schema from FastAPI
    openapi_schema = get_openapi(
        title="SpoutBreeze API",
        version="1.0.0",
        description="SpoutBreeze API documentation",
        routes=app.routes,
    )
    
    # Make sure components exist
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    # Preserve existing schemas if they exist
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}
        
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Apply security globally
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

origins = [
    "http://localhost:3000",
    "https://bbb3.riadvice.ovh",
    "http://localhost:8080"
]
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint that returns a welcome message
    """
    return {"message": "Welcome to SpoutBreeze API"}

# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(stream_router)
app.include_router(broadcaster_router)
app.include_router(bbb_router)

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
                logger.info(f"[TwitchIRC] Sending message: {message}")
            else:
                await chat_manager.broadcast(data)
    except WebSocketDisconnect:
        chat_manager.disconnect(websocket)
        logger.info("[Chat] Client disconnected")

