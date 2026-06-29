from pydantic import BaseModel


class UserSummary(BaseModel):
    id: str
    email: str
    full_name: str | None = None
