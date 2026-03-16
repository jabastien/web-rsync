from datetime import datetime
from pydantic import BaseModel, field_validator


class HostBase(BaseModel):
    name: str
    hostname: str
    port: int = 22
    username: str
    ssh_key_path: str | None = None


class HostCreate(HostBase):
    pass


class HostUpdate(BaseModel):
    name: str | None = None
    hostname: str | None = None
    port: int | None = None
    username: str | None = None
    ssh_key_path: str | None = None


class HostRead(HostBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeployKeyRequest(BaseModel):
    password: str
