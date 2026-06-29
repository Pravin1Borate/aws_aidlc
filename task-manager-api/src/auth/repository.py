from src.auth.schemas import User
from src.core.storage import JsonFileStorage


class UserRepository:
    def __init__(self, storage: JsonFileStorage) -> None:
        self._storage = storage

    def find_by_email(self, email: str) -> User | None:
        for record in self._storage.read_all():
            if record.get("email", "").lower() == email.lower():
                return User.model_validate(record)
        return None

    def find_by_id(self, user_id: str) -> User | None:
        record = self._storage.find_by_id(user_id)
        if record is None:
            return None
        return User.model_validate(record)

    def save(self, user: User) -> User:
        self._storage.upsert(user.model_dump(mode="json"))
        return user
