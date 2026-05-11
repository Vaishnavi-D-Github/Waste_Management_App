from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    latitude: float
    longitude: float


class MunicipalRequestOut(BaseModel):
    id: int
    decision: str
    waste: int
    delay: int
    density: int
    area: int
    lat: float
    lon: float
    bin_lat: float | None
    bin_lon: float | None
    status: str
    priority: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class MunicipalStatusUpdate(BaseModel):
    status: str
    notes: str | None = None
