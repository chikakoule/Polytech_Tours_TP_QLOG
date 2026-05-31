"""Endpoints d'authentification (§3.3.2)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import authenticate
from app.database import get_db
from app.models import User
from app.schemas import ChangePasswordRequest, LoginRequest
from app.security import (
    get_current_user,
    hash_password,
    password_meets_policy,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return authenticate(db, payload.email.strip().lower(), payload.password)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe actuel est incorrect",
        )
    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Les deux mots de passe ne correspondent pas",
        )
    if payload.new_password == payload.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nouveau mot de passe doit être différent de l'ancien",
        )
    if not password_meets_policy(payload.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Le mot de passe doit contenir au moins 12 caractères avec "
                "majuscule, minuscule, chiffre et caractère spécial"
            ),
        )

    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    db.commit()
    return {"message": "Mot de passe modifié avec succès"}


@router.post("/logout")
def logout(user: User = Depends(get_current_user)):
    # JWT stateless : la déconnexion est gérée côté client (suppression du token).
    return {"message": "Déconnexion réussie"}
