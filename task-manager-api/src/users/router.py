from fastapi import APIRouter, Depends, Request

from src.auth.schemas import UserResponse
from src.core.rate_limiter import limiter
from src.dependencies import get_current_user, get_user_service
from src.users.schemas import UserSummary
from src.users.service import UserService

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/", response_model=list[UserSummary])
@limiter.limit("100/minute")
async def list_users(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    current_user: UserResponse = Depends(get_current_user),
) -> list[UserSummary]:
    return user_service.list_users()


@user_router.get("/{user_id}", response_model=UserSummary)
@limiter.limit("100/minute")
async def get_user(
    request: Request,
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    current_user: UserResponse = Depends(get_current_user),
) -> UserSummary:
    return user_service.get_by_id(user_id)
