"""Endpoints événements (§3.3.6)."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Event, Match, Team, User
from app.schemas import EventCreate, EventUpdate
from app.security import get_current_user, require_admin
from app.services.serializers import event_out

router = APIRouter(prefix="/events", tags=["events"])


def _validate_matches(db: Session, matches) -> None:
    if not 1 <= len(matches) <= 3:
        raise HTTPException(status_code=400, detail="Un événement contient 1 à 3 matchs")

    courts: set[int] = set()
    teams_used: set[int] = set()
    for m in matches:
        if not 1 <= m.court_number <= 10:
            raise HTTPException(
                status_code=400, detail="Le numéro de piste doit être entre 1 et 10"
            )
        if m.team1_id == m.team2_id:
            raise HTTPException(status_code=400, detail="Une équipe ne peut s'affronter elle-même")
        if m.court_number in courts:
            raise HTTPException(
                status_code=400,
                detail=f"La piste {m.court_number} est utilisée deux fois dans l'événement",
            )
        courts.add(m.court_number)
        for tid in (m.team1_id, m.team2_id):
            if tid in teams_used:
                raise HTTPException(
                    status_code=400,
                    detail="Une équipe ne peut jouer qu'un seul match par événement",
                )
            teams_used.add(tid)
        for tid in (m.team1_id, m.team2_id):
            if db.query(Team).filter(Team.id == tid).first() is None:
                raise HTTPException(status_code=404, detail="Équipe introuvable")


@router.get("")
def list_events(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    month: str | None = Query(default=None, description="YYYY-MM"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Event)
    if start_date is not None:
        q = q.filter(Event.event_date >= start_date)
    if end_date is not None:
        q = q.filter(Event.event_date <= end_date)
    if month is not None:
        try:
            year, mon = month.split("-")
            first = date(int(year), int(mon), 1)
            last = date(int(year) + (mon == "12"), (int(mon) % 12) + 1, 1)
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="Format de mois invalide (YYYY-MM)")
        q = q.filter(Event.event_date >= first, Event.event_date < last)
    events = q.order_by(Event.event_date, Event.event_time).all()
    return {"events": [event_out(e) for e in events]}


@router.get("/{event_id}")
def get_event(
    event_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Événement introuvable")
    return event_out(event)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    _validate_matches(db, payload.matches)

    event = Event(event_date=payload.event_date, event_time=payload.event_time)
    db.add(event)
    db.flush()
    for m in payload.matches:
        db.add(
            Match(
                event_id=event.id,
                team1_id=m.team1_id,
                team2_id=m.team2_id,
                court_number=m.court_number,
                status="A_VENIR",
            )
        )
    db.commit()
    db.refresh(event)
    return event_out(event)


@router.put("/{event_id}")
def update_event(
    event_id: int,
    payload: EventUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Événement introuvable")
    if payload.event_date < date.today():
        raise HTTPException(
            status_code=400,
            detail="La date doit être postérieure ou égale à aujourd'hui",
        )
    event.event_date = payload.event_date
    event.event_time = payload.event_time
    db.commit()
    db.refresh(event)
    return event_out(event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Événement introuvable")
    # Suppression possible uniquement si aucun match n'a eu lieu (tous A_VENIR).
    has_non_pending = any(m.status != "A_VENIR" for m in event.matches)
    if has_non_pending:
        raise HTTPException(
            status_code=409,
            detail="Suppression impossible : l'événement contient des matchs joués ou annulés",
        )
    db.delete(event)
    db.commit()
    return None
