from src.core.errors import NotFoundError
from src.users.repository import UserReadRepository
from src.users.schemas import UserSummary


class UserService:
    def __init__(self, user_read_repo: UserReadRepository) -> None:
        self._repo = user_read_repo

    def list_users(self) -> list[UserSummary]:
        return self._repo.find_all()

    def get_by_id(self, user_id: str) -> UserSummary:
        user = self._repo.find_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user
