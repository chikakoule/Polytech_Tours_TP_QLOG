"""Validations métier réutilisables (formats §3.4)."""
import re

LICENSE_RE = re.compile(r"^L\d{6}$")
EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
NAME_RE = re.compile(r"^[a-zA-ZÀ-ÿ\s'-]{2,50}$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

# Forme générale : "X-Y, X-Y" ou "X-Y, X-Y, X-Y"
SCORE_SHAPE_RE = re.compile(r"^(\d+-\d+)(,\s*\d+-\d+){1,2}$")


def is_valid_license(value: str) -> bool:
    return bool(LICENSE_RE.match(value or ""))


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value or ""))


def is_valid_name(value: str) -> bool:
    return bool(NAME_RE.match(value or ""))


def is_valid_time(value: str) -> bool:
    return bool(TIME_RE.match(value or ""))


def validate_score(score: str) -> bool:
    """Valide un score de padel.

    Vérifie le format "X-Y, X-Y" (2 ou 3 sets).
    Exemples valides : "6-4, 6-3", "6-4, 3-6, 7-5".
    """
    if not score:
        return False
    return bool(SCORE_SHAPE_RE.match(score.strip()))
