import uuid

from pydantic import BaseModel


class IdentityResponse(BaseModel):
    account_id: uuid.UUID
    subject: str
    session_id: str | None = None
