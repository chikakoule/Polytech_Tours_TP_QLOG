"""Endpoints poules (§3.3.5). Une poule = exactement 6 équipes."""
import bleach
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Match, Pool, Team, User
from app.schemas import PoolCreate, PoolUpdate
from app.security import get_current_user, require_admin
from app.services.serializers import team_out

router = APIRouter(prefix="/pools", tags=["pools"])

REQUIRED_TEAMS = 6


def _clean(value: str) -> str:
    return bleach.clean(value, tags=[], strip=True)


def _pool_out(pool: Pool) -> dict:
    return {
        "id": pool.id,
        "name": pool.name,
        "teams_count": len(pool.teams),
        "teams": [team_out(t) for t in pool.teams],
    }


def _pool_has_played(db: Session, pool_id: int) -> bool:
    team_ids = [t.id for t in db.query(Team).filter(Team.pool_id == pool_id).all()]
    if not team_ids:
        return False
    return (
        db.query(Match)
        .filter((Match.team1_id.in_(team_ids)) | (Match.team2_id.in_(team_ids)))
        .filter(Match.status == "TERMINE")
        .first()
        is not None
    )


def _load_exactly_six(db: Session, team_ids: list[int]) -> list[Team]:
    if len(set(team_ids)) != REQUIRED_TEAMS:
        raise HTTPException(
            status_code=400, detail="Une poule doit contenir exactement 6 équipes"
        )
    teams = db.query(Team).filter(Team.id.in_(team_ids)).all()
    if len(teams) != REQUIRED_TEAMS:
        raise HTTPException(status_code=404, detail="Une ou plusieurs équipes sont introuvables")
    return teams


@router.get("")
def list_pools(
    _: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    pools = db.query(Pool).order_by(Pool.name).all()
    return {"pools": [_pool_out(p) for p in pools]}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_pool(
    payload: PoolCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    name = _clean(payload.name)
    if db.query(Pool).filter(Pool.name == name).first():
        raise HTTPException(status_code=409, detail="Une poule porte déjà ce nom")
    teams = _load_exactly_six(db, payload.team_ids)
    pool = Pool(name=name)
    db.add(pool)
    db.flush()
    for t in teams:
        t.pool_id = pool.id
    db.commit()
    db.refresh(pool)
    return _pool_out(pool)


@router.put("/{pool_id}")
def update_pool(
    pool_id: int,
    payload: PoolUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    pool = db.query(Pool).filter(Pool.id == pool_id).first()
    if pool is None:
        raise HTTPException(status_code=404, detail="Poule introuvable")
    if _pool_has_played(db, pool_id):
        raise HTTPException(
            status_code=409,
            detail="Modification impossible : des matchs ont déjà été joués dans cette poule",
        )
    teams = _load_exactly_six(db, payload.team_ids)
    if payload.name is not None:
        new_name = _clean(payload.name)
        existing = db.query(Pool).filter(Pool.name == new_name, Pool.id != pool_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Une poule porte déjà ce nom")
        pool.name = new_name
    # Détache les anciennes équipes, rattache les nouvelles.
    for t in db.query(Team).filter(Team.pool_id == pool_id).all():
        t.pool_id = None
    for t in teams:
        t.pool_id = pool.id
    db.commit()
    db.refresh(pool)
    return _pool_out(pool)


@router.delete("/{pool_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pool(
    pool_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    pool = db.query(Pool).filter(Pool.id == pool_id).first()
    if pool is None:
        raise HTTPException(status_code=404, detail="Poule introuvable")
    if _pool_has_played(db, pool_id):
        raise HTTPException(
            status_code=409,
            detail="Suppression impossible : des matchs ont déjà été joués dans cette poule",
        )
    for t in db.query(Team).filter(Team.pool_id == pool_id).all():
        t.pool_id = None
    db.delete(pool)
    db.commit()
    return None
