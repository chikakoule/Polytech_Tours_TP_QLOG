"""Sécurité : hachage bcrypt, génération/validation JWT, dépendances d'auth.

NB pédagogique : la vérification de l'expiration JWT (BUG-S5) et le contrôle
de rôle (BUG-S1) sont concentrés ici et dans les routers /admin.
Version SAINE : exp vérifiée, require_role renvoie 403.
"""
import secrets
import string
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

# Politique de mot de passe : >= 12 caractères, maj, min, chiffre, spécial.
_SPECIALS = "!@#$%^&*()-_=+[]{};:,.<>?/|"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def password_meets_policy(password: str) -> bool:
    if len(password) < 12:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in _SPECIALS for c in password)
    return has_upper and has_lower and has_digit and has_special


def generate_temporary_password(length: int = 16) -> str:
    """Génère un mot de passe temporaire respectant la politique."""
    while True:
        alphabet = string.ascii_letters + string.digits + _SPECIALS
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if password_meets_policy(pwd):
            return pwd


def create_access_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """Décode et valide le JWT. L'expiration (exp) est vérifiée par défaut."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dépendance : exige un JWT valide et renvoie l'utilisateur courant."""
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise invalid
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise invalid

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise invalid
    return user


def require_role(*roles: str):
    """Dépendance d'autorisation : renvoie 403 si le rôle est insuffisant."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès interdit : rôle insuffisant",
            )
        return user

    return checker


# Dépendance pratique pour les routes réservées aux administrateurs.
require_admin = require_role("ADMINISTRATEUR")
