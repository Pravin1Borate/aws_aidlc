from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.auth.repository import UserRepository
from src.auth.schemas import UserResponse
from src.auth.service import AuthService
from src.config import settings
from src.core.storage import JsonFileStorage
from src.tasks.repository import TaskRepository
from src.tasks.service import TaskService
from src.users.repository import UserReadRepository
from src.users.service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_user_repository() -> UserRepository:
    storage = JsonFileStorage(f"{settings.DATA_DIR}/users.json")
    return UserRepository(storage)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(user_repo)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    return auth_service.get_current_user(token)


def get_task_repository() -> TaskRepository:
    storage = JsonFileStorage(f"{settings.DATA_DIR}/tasks.json")
    return TaskRepository(storage)


def get_user_read_repository() -> UserReadRepository:
    storage = JsonFileStorage(f"{settings.DATA_DIR}/users.json")
    return UserReadRepository(storage)


def get_task_service(
    task_repo: TaskRepository = Depends(get_task_repository),
    user_read_repo: UserReadRepository = Depends(get_user_read_repository),
) -> TaskService:
    return TaskService(task_repo, user_read_repo)


def get_user_service(
    user_read_repo: UserReadRepository = Depends(get_user_read_repository),
) -> UserService:
    return UserService(user_read_repo)
