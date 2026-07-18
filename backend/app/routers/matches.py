"""Endpoints matchs (§3.3.7)."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Event, Match, Player, Team, User
from app.schemas import MatchCreate, MatchUpdate
from app.security import get_current_user, require_admin
from app.services.rankings import player_team_ids
from app.services.serializers import match_out
from app.validators import validate_score

router = APIRouter(prefix="/matches", tags=["matches"])


def _court_conflict(
    db: Session,
    event_date: date,
    event_time: str,
    court: int,
    exclude_match: int | None = None,
) -> bool:
    """Vrai si la piste est déjà occupée à ce créneau (date + heure)."""
    q = (
        db.query(Match)
        .join(Event, Match.event_id == Event.id)
        .filter(Event.event_date == event_date)
        .filter(Event.event_time == event_time)
        .filter(Match.court_number == court)
        .filter(Match.status != "ANNULE")
    )
    if exclude_match is not None:
        q = q.filter(Match.id != exclude_match)
    return q.first() is not None


def _get_or_create_event(db: Session, event_date: date, event_time: str) -> Event:
    event = (
        db.query(Event)
        .filter(Event.event_date == event_date, Event.event_time == event_time)
        .first()
    )
    if event is None:
        event = Event(event_date=event_date, event_time=event_time)
        db.add(event)
        db.flush()
    return event


@router.get("")
def list_matches(
    upcoming: bool = Query(default=False),
    team_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    my_matches: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Match).join(Event, Match.event_id == Event.id)

    if upcoming:
        today = date.today()
        q = q.filter(Event.event_date >= today, Event.event_date <= today + timedelta(days=30))

    if team_id is not None:
        q = q.filter((Match.team1_id == team_id) | (Match.team2_id == team_id))

    if status_filter is not None:
        q = q.filter(Match.status == status_filter)

    if my_matches:
        player = db.query(Player).filter(Player.user_id == user.id).first()
        team_ids = player_team_ids(db, player.id) if player else []
        if team_ids:
            q = q.filter((Match.team1_id.in_(team_ids)) | (Match.team2_id.in_(team_ids)))
        else:
            q = q.filter(False)  # aucun match si le joueur n'a pas d'équipe

    matches = q.order_by(Event.event_date, Event.event_time).all()
    return {"matches": [match_out(m) for m in matches], "total": len(matches)}


@router.get("/{match_id}")
def get_match(
    match_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if match is None:
        raise HTTPException(status_code=404, detail="Match introuvable")
    return match_out(match)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_match(
    payload: MatchCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if payload.event_date < date.today():
        raise HTTPException(
            status_code=400, detail="La date doit être postérieure ou égale à aujourd'hui"
        )
    if payload.team1_id == payload.team2_id:
        raise HTTPException(status_code=400, detail="Une équipe ne peut s'affronter elle-même")
    for tid in (payload.team1_id, payload.team2_id):
        if db.query(Team).filter(Team.id == tid).first() is None:
            raise HTTPException(status_code=404, detail="Équipe introuvable")

    event = _get_or_create_event(db, payload.event_date, payload.event_time)
    match = Match(
        event_id=event.id,
        team1_id=payload.team1_id,
        team2_id=payload.team2_id,
        court_number=payload.court_number,
        status="A_VENIR",
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match_out(match)


@router.put("/{match_id}")
def update_match(
    match_id: int,
    payload: MatchUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if match is None:
        raise HTTPException(status_code=404, detail="Match introuvable")

    new_status = payload.status or match.status

    # Modification de la date/heure : seulement si le match n'a pas encore eu lieu.
    new_date = payload.event_date or match.event.event_date
    new_time = payload.event_time or match.event.event_time
    if payload.event_date is not None or payload.event_time is not None:
        if match.status != "A_VENIR":
            raise HTTPException(
                status_code=409,
                detail="Impossible de modifier la date d'un match qui n'est pas A_VENIR",
            )

    new_court = payload.court_number or match.court_number
    if _court_conflict(db, new_date, new_time, new_court, exclude_match=match.id):
        raise HTTPException(
            status_code=409, detail=f"La piste {new_court} est déjà occupée à ce créneau"
        )

    # Saisie / validation des scores.
    if new_status == "TERMINE":
        score1 = payload.score_team1 if payload.score_team1 is not None else match.score_team1
        score2 = payload.score_team2 if payload.score_team2 is not None else match.score_team2
        if not score1 or not score2:
            raise HTTPException(
                status_code=400, detail="Un match terminé doit comporter les deux scores"
            )
        if not validate_score(score1) or not validate_score(score2):
            raise HTTPException(
                status_code=400, detail="Format de score invalide (ex: 6-4, 6-3)"
            )
        match.score_team1 = score1
        match.score_team2 = score2

    # Mise à jour de l'événement (date/heure) le cas échéant.
    if payload.event_date is not None or payload.event_time is not None:
        event = _get_or_create_event(db, new_date, new_time)
        match.event_id = event.id

    if payload.court_number is not None:
        match.court_number = payload.court_number
    match.status = new_status
    db.commit()
    db.refresh(match)
    return match_out(match)


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_match(
    match_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if match is None:
        raise HTTPException(status_code=404, detail="Match introuvable")
    db.delete(match)
    db.commit()
    return None
