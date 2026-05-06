import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routes import user, prediction

Base.metadata.create_all(bind=engine)

app = FastAPI()

_default_origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]
_extra = os.getenv("CORS_ORIGINS", "").strip()
_origins = _default_origins + ([o.strip() for o in _extra.split(",") if o.strip()] if _extra else [])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(prediction.router)