from fastapi import APIRouter, Depends, Request

from src.auth.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
from src.auth.service import AuthService
from src.core.rate_limiter import limiter
from src.dependencies import get_auth_service, get_current_user, oauth2_scheme

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("20/minute")
async def register(
    request: Request,
    data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    return auth_service.register(data)


@auth_router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
async def login(
    request: Request,
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return auth_service.login(data)


@auth_router.post("/logout", status_code=200)
@limiter.limit("100/minute")
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    auth_service.logout(token)
    return {"message": "Logged out successfully"}


@auth_router.get("/me", response_model=UserResponse)
@limiter.limit("100/minute")
async def get_me(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    return current_user
