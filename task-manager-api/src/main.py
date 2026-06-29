from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.auth.router import auth_router
from src.config import settings
from src.core.errors import AppException
from src.core.health import health_router
from src.core.logging import configure_logging, get_logger
from src.core.middleware import CorrelationIdMiddleware
from src.core.rate_limiter import limiter
from src.tasks.router import task_router
from src.users.router import user_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.LOG_LEVEL)
    if not settings.JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY must be set in environment")
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
    logger.info("startup_complete", extra={"data_dir": settings.DATA_DIR})
    yield
    logger.info("shutdown")


app = FastAPI(title="Task Manager API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter

# NOTE: Permissive CORS for local development only. Tighten before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(AppException)
async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(exc.message, extra={"status_code": exc.status_code})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(RateLimitExceeded)
async def handle_rate_limit(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


@app.exception_handler(Exception)
async def handle_unhandled(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


app.include_router(auth_router)
app.include_router(health_router)
app.include_router(task_router)
app.include_router(user_router)


if __name__ == "__main__":
    uvicorn.run("src.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
