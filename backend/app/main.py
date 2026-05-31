"""Point d'entrée FastAPI — Corpo Padel API."""
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import (
    admin,
    auth,
    events,
    matches,
    players,
    pools,
    profile,
    results,
    teams,
)

API_PREFIX = "/api/v1"

app = FastAPI(
    title="Corpo Padel API",
    version="1.0.0",
    description="API de gestion de tournois de padel corporatifs.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """En-têtes de sécurité (§4.2.2)."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    os.makedirs(settings.upload_dir, exist_ok=True)


# Fichiers statiques (photos de profil).
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/")
def root():
    return {"name": "Corpo Padel API", "docs": "/docs", "api": API_PREFIX}


@app.get(f"{API_PREFIX}/health")
def health():
    return {"status": "ok"}


for r in (auth, players, teams, pools, events, matches, results, profile, admin):
    app.include_router(r.router, prefix=API_PREFIX)
