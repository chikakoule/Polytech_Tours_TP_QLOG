"""Endpoints équipes (§3.3.4)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Match, Player, Team, User
from app.schemas import TeamCreate, TeamUpdate
from app.security import get_current_user, require_admin
from app.services.serializers import team_out

router = APIRouter(prefix="/teams", tags=["teams"])


def _team_has_played(db: Session, team_id: int) -> bool:
    return (
        db.query(Match)
        .filter((Match.team1_id == team_id) | (Match.team2_id == team_id))
        .filter(Match.status == "TERMINE")
        .first()
        is not None
    )


def _player_in_other_team(db: Session, player_id: int, exclude_team: int | None) -> bool:
    q = db.query(Team).filter(
        (Team.player1_id == player_id) | (Team.player2_id == player_id)
    )
    if exclude_team is not None:
        q = q.filter(Team.id != exclude_team)
    return q.first() is not None


def _validate_players(db: Session, payload, exclude_team: int | None = None) -> tuple[Player, Player]:
    if payload.player1_id == payload.player2_id:
        raise HTTPException(status_code=400, detail="Les deux joueurs doivent être distincts")
    p1 = db.query(Player).filter(Player.id == payload.player1_id).first()
    p2 = db.query(Player).filter(Player.id == payload.player2_id).first()
    if p1 is None or p2 is None:
        raise HTTPException(status_code=404, detail="Joueur introuvable")
    if p1.company.lower() != p2.company.lower():
        raise HTTPException(
            status_code=400,
            detail="Les deux joueurs doivent appartenir à la même entreprise",
        )
    for pid in (payload.player1_id, payload.player2_id):
        if _player_in_other_team(db, pid, exclude_team):
            raise HTTPException(
                status_code=409,
                detail="Un joueur ne peut appartenir qu'à une seule équipe par saison",
            )
    return p1, p2


@router.get("")
def list_teams(
    pool_id: int | None = Query(default=None),
    company: str | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Team)
    if pool_id is not None:
        q = q.filter(Team.pool_id == pool_id)
    if company is not None:
        q = q.filter(Team.company == company)
    teams = q.all()
    return {"teams": [team_out(t) for t in teams], "total": len(teams)}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    _validate_players(db, payload)
    team = Team(
        company=payload.company,
        player1_id=payload.player1_id,
        player2_id=payload.player2_id,
        pool_id=payload.pool_id,
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return team_out(team)


@router.put("/{team_id}")
def update_team(
    team_id: int,
    payload: TeamUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=404, detail="Équipe introuvable")
    if _team_has_played(db, team_id):
        raise HTTPException(
            status_code=409,
            detail="Modification impossible : l'équipe a déjà joué des matchs",
        )
    _validate_players(db, payload, exclude_team=team_id)
    if payload.company is not None:
        team.company = payload.company
    team.player1_id = payload.player1_id
    team.player2_id = payload.player2_id
    team.pool_id = payload.pool_id
    db.commit()
    db.refresh(team)
    return team_out(team)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=404, detail="Équipe introuvable")
    if _team_has_played(db, team_id):
        raise HTTPException(
            status_code=409,
            detail="Suppression impossible : l'équipe a déjà joué des matchs",
        )
    db.delete(team)
    db.commit()
    return None
