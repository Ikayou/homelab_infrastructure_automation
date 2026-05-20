from pydantic import BaseModel


class KeycloakUserCreate(BaseModel):
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str


class KeycloakUserUpdate(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    enabled: bool | None = None