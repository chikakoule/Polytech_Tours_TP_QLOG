"""Schémas Pydantic v2 pour les requêtes (validation §3.4 / §7.6).

Les réponses à structure riche (équipes imbriquées, classement, résultats) sont
construites par les sérialiseurs de app/services pour coller aux exemples JSON
du cahier des charges.
"""
from datetime import date

from pydantic import BaseModel, field_validator

from app import validators


# ─────────────────────────── Auth ───────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


# ────────────────────────── Players ─────────────────────────
class PlayerCreate(BaseModel):
    first_name: str
    last_name: str
    company: str
    license_number: str
    email: str

    @field_validator("first_name", "last_name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        v = v.strip()
        if not validators.is_valid_name(v):
            raise ValueError("2 à 50 caractères, lettres uniquement")
        return v

    @field_validator("company")
    @classmethod
    def _check_company(cls, v: str) -> str:
        v = v.strip()
        if not 2 <= len(v) <= 100:
            raise ValueError("L'entreprise doit faire 2 à 100 caractères")
        return v

    @field_validator("license_number")
    @classmethod
    def _check_license(cls, v: str) -> str:
        v = v.strip()
        if not validators.is_valid_license(v):
            raise ValueError("Le numéro de licence doit être au format LXXXXXX")
        return v

    @field_validator("email")
    @classmethod
    def _check_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not validators.is_valid_email(v):
            raise ValueError("Format d'email invalide")
        return v


class PlayerUpdate(BaseModel):
    """Modification admin : tout sauf licence et email (§2.6.1)."""

    first_name: str
    last_name: str
    company: str

    @field_validator("first_name", "last_name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        v = v.strip()
        if not validators.is_valid_name(v):
            raise ValueError("2 à 50 caractères, lettres uniquement")
        return v

    @field_validator("company")
    @classmethod
    def _check_company(cls, v: str) -> str:
        v = v.strip()
        if not 2 <= len(v) <= 100:
            raise ValueError("L'entreprise doit faire 2 à 100 caractères")
        return v


# ─────────────────────────── Teams ──────────────────────────
class TeamCreate(BaseModel):
    company: str
    player1_id: int
    player2_id: int
    pool_id: int | None = None

    @field_validator("company")
    @classmethod
    def _check_company(cls, v: str) -> str:
        v = v.strip()
        if not 2 <= len(v) <= 100:
            raise ValueError("L'entreprise doit faire 2 à 100 caractères")
        return v


class TeamUpdate(BaseModel):
    company: str | None = None
    player1_id: int
    player2_id: int
    pool_id: int | None = None


# ─────────────────────────── Pools ──────────────────────────
class PoolCreate(BaseModel):
    name: str
    team_ids: list[int]

    @field_validator("name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le nom de la poule est obligatoire")
        return v


class PoolUpdate(BaseModel):
    name: str | None = None
    team_ids: list[int]


# ────────────────────────── Matches ─────────────────────────
class MatchInEvent(BaseModel):
    court_number: int
    team1_id: int
    team2_id: int


class EventCreate(BaseModel):
    event_date: date
    event_time: str
    matches: list[MatchInEvent]

    @field_validator("event_time")
    @classmethod
    def _check_time(cls, v: str) -> str:
        if not validators.is_valid_time(v):
            raise ValueError("L'heure doit être au format HH:MM")
        return v


class EventUpdate(BaseModel):
    event_date: date
    event_time: str

    @field_validator("event_time")
    @classmethod
    def _check_time(cls, v: str) -> str:
        if not validators.is_valid_time(v):
            raise ValueError("L'heure doit être au format HH:MM")
        return v


class MatchCreate(BaseModel):
    event_date: date
    event_time: str
    court_number: int
    team1_id: int
    team2_id: int

    @field_validator("event_time")
    @classmethod
    def _check_time(cls, v: str) -> str:
        if not validators.is_valid_time(v):
            raise ValueError("L'heure doit être au format HH:MM")
        return v

    @field_validator("court_number")
    @classmethod
    def _check_court(cls, v: int) -> int:
        if not 1 <= v <= 10:
            raise ValueError("Le numéro de piste doit être entre 1 et 10")
        return v


class MatchUpdate(BaseModel):
    event_date: date | None = None
    event_time: str | None = None
    court_number: int | None = None
    status: str | None = None
    score_team1: str | None = None
    score_team2: str | None = None

    @field_validator("event_time")
    @classmethod
    def _check_time(cls, v: str | None) -> str | None:
        if v is not None and not validators.is_valid_time(v):
            raise ValueError("L'heure doit être au format HH:MM")
        return v

    @field_validator("court_number")
    @classmethod
    def _check_court(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 10:
            raise ValueError("Le numéro de piste doit être entre 1 et 10")
        return v

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str | None) -> str | None:
        if v is not None and v not in ("A_VENIR", "TERMINE", "ANNULE"):
            raise ValueError("Statut invalide")
        return v


# ────────────────────────── Profile ─────────────────────────
class ProfileUpdate(BaseModel):
    first_name: str
    last_name: str
    email: str
    birth_date: date | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        v = v.strip()
        if not validators.is_valid_name(v):
            raise ValueError("2 à 50 caractères, lettres uniquement")
        return v

    @field_validator("email")
    @classmethod
    def _check_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not validators.is_valid_email(v):
            raise ValueError("Format d'email invalide")
        return v

    @field_validator("birth_date")
    @classmethod
    def _check_birth_date(cls, v: date | None) -> date | None:
        if v is None:
            return v
        today = date.today()
        if v > today:
            raise ValueError("La date de naissance ne peut pas être dans le futur")
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 16:
            raise ValueError("L'utilisateur doit avoir au moins 16 ans")
        return v


# ─────────────────────────── Admin ──────────────────────────
class AccountCreate(BaseModel):
    player_id: int
    role: str = "JOUEUR"

    @field_validator("role")
    @classmethod
    def _check_role(cls, v: str) -> str:
        if v not in ("JOUEUR", "ADMINISTRATEUR"):
            raise ValueError("Rôle invalide")
        return v
