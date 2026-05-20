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
    
class ContainerResponse(BaseModel):
    name: str
    id: str
    status: str
    image: list[str]
    
class ContainerStatsResponse(BaseModel):
    name: str
    status: str
    cpu_percent: float
    memory_usage_mb: float
    memory_limit_mb: float