"""Logique d'authentification et protection anti-brute force (§2.1.3 / §4.2.4)."""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models import LoginAttempt, User
from app.security import create_access_token, verify_password


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_or_create_attempt(db: Session, email: str) -> LoginAttempt:
    attempt = db.query(LoginAttempt).filter(LoginAttempt.email == email).first()
    if attempt is None:
        attempt = LoginAttempt(email=email, attempts_count=0)
        db.add(attempt)
        db.flush()
    return attempt


def _ensure_not_locked(attempt: LoginAttempt) -> None:
    """Lève 403 si le compte est actuellement verrouillé."""
    if attempt.locked_until is not None:
        locked_until = attempt.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if locked_until > _now():
            remaining = int((locked_until - _now()).total_seconds() // 60) + 1
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "detail": "Compte bloqué",
                    "locked_until": attempt.locked_until.isoformat(),
                    "minutes_remaining": remaining,
                },
            )


def authenticate(db: Session, email: str, password: str) -> dict:
    """Authentifie un utilisateur en appliquant l'anti-brute force.

    Retourne le payload de réponse (token + user) ou lève une HTTPException
    avec le code et le corps adaptés (401 / 403).
    """
    attempt = _get_or_create_attempt(db, email)
    _ensure_not_locked(attempt)

    # Le verrou a expiré : on repart d'un compteur propre.
    if attempt.locked_until is not None:
        locked_until = attempt.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if locked_until <= _now():
            attempt.attempts_count = 0
            attempt.locked_until = None

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        error_message = "Utilisateur inconnu"
        credentials_ok = False
    elif not verify_password(password, user.password_hash):
        error_message = "Mot de passe incorrect"
        credentials_ok = False
    else:
        credentials_ok = True

    if not credentials_ok:
        attempt.attempts_count += 1
        attempt.last_attempt = _now()

        if attempt.attempts_count > settings.max_login_attempts:
            attempt.locked_until = _now() + timedelta(minutes=settings.lockout_minutes)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "detail": "Compte bloqué",
                    "locked_until": attempt.locked_until.isoformat(),
                    "minutes_remaining": settings.lockout_minutes,
                },
            )

        remaining = settings.max_login_attempts - attempt.attempts_count
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": error_message, "attempts_remaining": remaining},
        )

    # Succès : réinitialisation du compteur.
    attempt.attempts_count = 0
    attempt.locked_until = None
    attempt.last_attempt = _now()
    db.commit()

    token = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "must_change_password": user.must_change_password,
        },
    }
