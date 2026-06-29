from src.core.storage import JsonFileStorage
from src.users.schemas import UserSummary


class UserReadRepository:
    def __init__(self, storage: JsonFileStorage) -> None:
        self._storage = storage

    def find_all(self) -> list[UserSummary]:
        return [self._to_summary(r) for r in self._storage.read_all()]

    def find_by_id(self, user_id: str) -> UserSummary | None:
        record = self._storage.find_by_id(user_id)
        return self._to_summary(record) if record else None

    def find_by_email(self, email: str) -> UserSummary | None:
        target = email.lower()
        for record in self._storage.read_all():
            if record.get("email", "").lower() == target:
                return self._to_summary(record)
        return None

    def _to_summary(self, record: dict) -> UserSummary:
        return UserSummary(
            id=record["id"],
            email=record["email"],
            full_name=record.get("full_name"),
        )
