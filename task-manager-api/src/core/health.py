import os
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import JSONResponse

health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get("/live")
async def liveness():
    return {"status": "ok", "service": "task-manager-api"}


@health_router.get("/ready")
async def readiness():
    from src.config import settings

    jwt_config_ok = bool(settings.JWT_SECRET_KEY)
    data_dir_path = Path(settings.DATA_DIR)
    data_dir_ok = data_dir_path.exists() and os.access(data_dir_path, os.W_OK)

    checks = {"jwt_config": jwt_config_ok, "data_dir": data_dir_ok}
    status = "ready" if all(checks.values()) else "degraded"
    return JSONResponse(
        status_code=200 if status == "ready" else 503,
        content={"status": status, "checks": checks},
    )
