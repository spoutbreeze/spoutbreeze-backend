from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers.auth_controller import router as auth_router
from app.controllers.bbb_controller import router as bbb_router

app = FastAPI(
    title="SpoutBreeze API",
    description="API for SpoutBreeze application with Keycloak integration",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(bbb_router)

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint that returns a welcome message
    """
    return {"message": "Welcome to SpoutBreeze API"}