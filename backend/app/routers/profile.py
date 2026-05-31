"""Endpoints profil utilisateur (§3.3.9)."""
import os
import uuid

import bleach
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Player, User
from app.schemas import ProfileUpdate
from app.security import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])

ALLOWED_PHOTO_EXT = {".jpg", ".jpeg", ".png"}


def _clean(value: str) -> str:
    return bleach.clean(value, tags=[], strip=True)


def _profile_payload(user: User, player: Player | None) -> dict:
    data = {"user": {"id": user.id, "email": user.email, "role": user.role}}
    if player is not None:
        data["player"] = {
            "id": player.id,
            "first_name": player.first_name,
            "last_name": player.last_name,
            "company": player.company,
            "license_number": player.license_number,
            "birth_date": player.birth_date.isoformat() if player.birth_date else None,
            "photo_url": player.photo_url,
        }
    return data


@router.get("/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.user_id == user.id).first()
    return _profile_payload(user, player)


@router.put("/me")
def update_me(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_email = payload.email
    if new_email != user.email:
        existing = db.query(User).filter(User.email == new_email).first()
        if existing is not None:
            raise HTTPException(status_code=409, detail="Email déjà utilisé")
        user.email = new_email

    player = db.query(Player).filter(Player.user_id == user.id).first()
    if player is not None:
        player.first_name = _clean(payload.first_name)
        player.last_name = _clean(payload.last_name)
        player.birth_date = payload.birth_date
    db.commit()
    return _profile_payload(user, player)


@router.post("/me/photo")
async def upload_photo(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    player = db.query(Player).filter(Player.user_id == user.id).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Profil joueur introuvable")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_PHOTO_EXT:
        raise HTTPException(
            status_code=400, detail="Format accepté : .jpg, .jpeg, .png"
        )

    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 2 Mo)")

    os.makedirs(settings.upload_dir, exist_ok=True)
    filename = f"profile_{player.id}_{uuid.uuid4().hex[:8]}{ext}"
    path = os.path.join(settings.upload_dir, filename)
    with open(path, "wb") as f:
        f.write(content)

    player.photo_url = f"/uploads/{filename}"
    db.commit()
    return {"photo_url": player.photo_url}


@router.delete("/me/photo", status_code=status.HTTP_200_OK)
def delete_photo(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    player = db.query(Player).filter(Player.user_id == user.id).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Profil joueur introuvable")
    player.photo_url = None
    db.commit()
    return {"message": "Photo supprimée"}
