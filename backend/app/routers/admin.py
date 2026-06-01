"""Endpoints d'administration des comptes (§3.3.10)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Player, User
from app.schemas import AccountCreate
from app.security import generate_temporary_password, get_current_user, hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/accounts/create", status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    player = db.query(Player).filter(Player.id == payload.player_id).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Joueur introuvable")
    if player.user_id is not None:
        raise HTTPException(status_code=409, detail="Ce joueur a déjà un compte")
    if db.query(User).filter(User.email == player.email).first():
        raise HTTPException(status_code=409, detail="Email déjà utilisé par un compte")

    temp_password = generate_temporary_password()
    user = User(
        email=player.email,
        password_hash=hash_password(temp_password),
        role=payload.role,
        is_active=True,
        must_change_password=True,
    )
    db.add(user)
    db.flush()
    player.user_id = user.id
    db.commit()

    return {
        "message": "Compte créé avec succès",
        "email": user.email,
        "temporary_password": temp_password,
        "warning": "Ce mot de passe ne sera affiché qu'une seule fois",
    }


@router.post("/accounts/{user_id}/reset-password")
def reset_password(
    user_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Compte introuvable")

    temp_password = generate_temporary_password()
    user.password_hash = hash_password(temp_password)
    user.must_change_password = True
    db.commit()

    return {
        "message": "Mot de passe réinitialisé",
        "temporary_password": temp_password,
        "warning": "Ce mot de passe ne sera affiché qu'une seule fois",
    }
