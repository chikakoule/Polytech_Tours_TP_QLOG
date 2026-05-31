"""Endpoints résultats et classement (§3.3.8)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Player, User
from app.security import get_current_user
from app.services.rankings import compute_my_results, compute_rankings

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/my-results")
def my_results(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    player = db.query(Player).filter(Player.user_id == user.id).first()
    if player is None:
        raise HTTPException(
            status_code=404, detail="Aucun profil joueur associé à ce compte"
        )
    return compute_my_results(db, player)


@router.get("/rankings")
def rankings(
    _: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return {"rankings": compute_rankings(db)}
