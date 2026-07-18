"""Endpoints joueurs (§3.3.3)."""
import bleach
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Player, Team, User
from app.schemas import PlayerCreate, PlayerUpdate
from app.security import get_current_user, require_admin
from app.services.serializers import player_full

router = APIRouter(prefix="/players", tags=["players"])


def _clean(value: str) -> str:
    """Défense en profondeur : retire tout balisage HTML des champs texte."""
    return bleach.clean(value, tags=[], strip=True)


@router.get("")
def list_players(
    _: User = Depends(require_admin), db: Session = Depends(get_db)
):
    players = db.query(Player).order_by(Player.last_name, Player.first_name).all()
    return {"players": [player_full(p) for p in players], "total": len(players)}


@router.get("/{player_id}")
def get_player(
    player_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    player = db.query(Player).filter(Player.id == player_id).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Joueur introuvable")
    return player_full(player)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_player(
    payload: PlayerCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(Player).filter(Player.license_number == payload.license_number).first():
        raise HTTPException(status_code=409, detail="Numéro de licence déjà utilisé")
    if db.query(Player).filter(Player.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email déjà utilisé")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email déjà utilisé")

    player = Player(
        first_name=_clean(payload.first_name),
        last_name=_clean(payload.last_name),
        company=_clean(payload.company),
        license_number=payload.license_number,
        email=payload.email,
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player_full(player)


@router.put("/{player_id}")
def update_player(
    player_id: int,
    payload: PlayerUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    player = db.query(Player).filter(Player.id == player_id).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Joueur introuvable")
    player.first_name = _clean(payload.first_name)
    player.last_name = _clean(payload.last_name)
    player.company = _clean(payload.company)
    db.commit()
    db.refresh(player)
    return player_full(player)


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(
    player_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    player = db.query(Player).filter(Player.id == player_id).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Joueur introuvable")
    in_team = (
        db.query(Team)
        .filter((Team.player1_id == player_id) | (Team.player2_id == player_id))
        .first()
    )
    if in_team is not None:
        raise HTTPException(
            status_code=409,
            detail="Suppression impossible : le joueur appartient à une équipe",
        )
    db.delete(player)
    db.commit()
    return None
