# Create a new file: app/controllers/health_controller.py
from fastapi import APIRouter, status, Response
from app.services.auth_service import AuthService
from app.config.database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy import text
from typing import Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api", tags=["Health"])

auth_service = AuthService()


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db), response: Response = None
) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {},
    }
    # Check Keycloak
    keycloak_healthy = auth_service.health_check()
    health_status["services"]["keycloak"] = {
        "status": "healthy" if keycloak_healthy else "unhealthy",
        "url": auth_service.settings.keycloak_server_url,
    }

    # Check Database
    try:
        await db.execute(text("SELECT 1"))
        health_status["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    # Overall status
    if not keycloak_healthy:
        health_status["status"] = "degraded"

    # Set appropriate status code
    if health_status["status"] != "healthy" and response:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return health_status


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Readiness check - determines if the application is ready to serve traffic
    """
    keycloak_ready = auth_service.health_check()

    try:
        await db.execute(text("SELECT 1"))
        db_ready = True
    except Exception:
        db_ready = False

    ready = keycloak_ready and db_ready

    return {
        "ready": ready,
        "services": {"keycloak": keycloak_ready, "database": db_ready},
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check - determines if the application is alive
    """
    return {"status": "alive", "timestamp": datetime.now().isoformat()}
