"""Point d'entrée FastAPI — Corpo Padel API."""
import os

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


_FIELD_LABELS = {
    "first_name": "Prénom",
    "last_name": "Nom",
    "company": "Entreprise",
    "license_number": "N° de licence",
    "email": "Email",
    "birth_date": "Date de naissance",
    "event_date": "Date",
    "event_time": "Heure",
    "court_number": "Numéro de piste",
    "team1_id": "Équipe 1",
    "team2_id": "Équipe 2",
    "name": "Nom de la poule",
    "team_ids": "Équipes",
    "current_password": "Mot de passe actuel",
    "new_password": "Nouveau mot de passe",
    "confirm_password": "Confirmation du mot de passe",
}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Transforme les erreurs Pydantic (422) en message clair et lisible.

    Conserve le code 422 et expose le détail brut sous `errors` pour le
    débogage, mais fournit un `detail` en français exploitable côté IHM.
    """
    messages: list[str] = []
    empty_fields: list[str] = []
    for err in exc.errors():
        loc = [p for p in err.get("loc", []) if p != "body"]
        field = loc[-1] if loc else ""
        label = _FIELD_LABELS.get(field, field)
        raw = err.get("msg", "Valeur invalide")
        # "Value error, <message>" -> "<message>"
        clean = raw.split("Value error, ", 1)[-1]
        if err.get("input") in ("", None) and err.get("type") in (
            "missing",
            "value_error",
            "string_too_short",
        ):
            empty_fields.append(label)
        else:
            messages.append(f"{label} : {clean}" if label else clean)

    if empty_fields and not messages:
        if len(empty_fields) >= 3:
            detail = "Aucun champ n'est renseigné, veuillez vérifier les valeurs avant de valider."
        else:
            detail = "Champ(s) obligatoire(s) manquant(s) : " + ", ".join(empty_fields) + "."
    else:
        for f in empty_fields:
            messages.insert(0, f"{f} : champ obligatoire")
        detail = " · ".join(messages) if messages else "Données invalides."

    # Nettoie les erreurs pour garantir un corps JSON sérialisable
    # (le ctx Pydantic peut contenir un objet exception non sérialisable).
    safe_errors = [
        {k: v for k, v in err.items() if k in ("type", "loc", "msg", "input")}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail, "errors": safe_errors},
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
