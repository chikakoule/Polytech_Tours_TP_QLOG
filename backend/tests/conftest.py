"""Fixtures pytest : base isolée par test, client httpx, helpers d'auth.

Cette suite est la RÉFÉRENCE ENSEIGNANT. Sur l'application saine, tout passe
au vert. Sur la version dégradée (10 bugs), les tests dédiés aux anomalies
(voir test_anomalies.py) échouent — ils servent de filet de détection.
"""
import os
import tempfile
import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Event, Match, Player, Pool, Team, User
from app.security import hash_password


@pytest.fixture()
def db_session():
    """Base SQLite sur fichier temporaire UNIQUE, supprimée après le test.

    Un fichier distinct par test garantit une isolation totale (pas de partage
    d'état possible entre tests, contrairement à une base ':memory:').
    """
    tmp_path = os.path.join(tempfile.gettempdir(), f"padel_test_{uuid.uuid4().hex}.db")
    engine = create_engine(
        f"sqlite:///{tmp_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        try:
            os.remove(tmp_path)
        except OSError:
            pass


@pytest.fixture()
def client(db_session):
    """Client de test FastAPI branché sur la base isolée."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ─────────────────────────── Helpers de données ───────────────────────────
ADMIN_EMAIL = "admin@padel.com"
ADMIN_PASSWORD = "Admin@2025!"
PLAYER_EMAIL = "joueur@padel.com"
PLAYER_PASSWORD = "Joueur@2025!"


@pytest.fixture()
def admin_user(db_session):
    user = User(
        email=ADMIN_EMAIL,
        password_hash=hash_password(ADMIN_PASSWORD),
        role="ADMINISTRATEUR",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(
        Player(
            first_name="Admin",
            last_name="Sys",
            company="Corpo Padel",
            license_number="L000001",
            email=ADMIN_EMAIL,
            user_id=user.id,
        )
    )
    db_session.commit()
    return user


@pytest.fixture()
def player_user(db_session):
    user = User(
        email=PLAYER_EMAIL,
        password_hash=hash_password(PLAYER_PASSWORD),
        role="JOUEUR",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    player = Player(
        first_name="Jean",
        last_name="Joueur",
        company="Tech Corp",
        license_number="L100001",
        email=PLAYER_EMAIL,
        user_id=user.id,
    )
    db_session.add(player)
    db_session.commit()
    return user


def _token(client, email, password):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture()
def admin_headers(client, admin_user):
    return {"Authorization": f"Bearer {_token(client, ADMIN_EMAIL, ADMIN_PASSWORD)}"}


@pytest.fixture()
def player_headers(client, player_user):
    return {"Authorization": f"Bearer {_token(client, PLAYER_EMAIL, PLAYER_PASSWORD)}"}


@pytest.fixture()
def make_players(db_session):
    """Crée n joueurs d'une même entreprise et renvoie leurs IDs."""

    def _make(company: str, count: int, start_license: int = 200000):
        ids = []
        for i in range(count):
            p = Player(
                first_name=f"Prenom{i}",
                last_name=f"Nom{i}",
                company=company,
                license_number=f"L{start_license + i:06d}",
                email=f"{company.lower().replace(' ', '')}{i}@ex.fr",
            )
            db_session.add(p)
            db_session.flush()
            ids.append(p.id)
        db_session.commit()
        return ids

    return _make


@pytest.fixture()
def make_team(db_session):
    """Crée une équipe directement en base et renvoie son ID."""

    def _make(company: str, p1: int, p2: int, pool_id: int | None = None):
        t = Team(company=company, player1_id=p1, player2_id=p2, pool_id=pool_id)
        db_session.add(t)
        db_session.commit()
        return t.id

    return _make


@pytest.fixture()
def make_match(db_session):
    """Crée un événement + un match en base, renvoie l'ID du match."""

    def _make(team1_id, team2_id, when: date, time_str="19:00", court=1, status="A_VENIR",
              score1=None, score2=None):
        ev = Event(event_date=when, event_time=time_str)
        db_session.add(ev)
        db_session.flush()
        m = Match(
            event_id=ev.id,
            team1_id=team1_id,
            team2_id=team2_id,
            court_number=court,
            status=status,
            score_team1=score1,
            score_team2=score2,
        )
        db_session.add(m)
        db_session.commit()
        return m.id

    return _make


@pytest.fixture()
def today():
    return date.today()


@pytest.fixture()
def tomorrow():
    return date.today() + timedelta(days=1)


@pytest.fixture()
def yesterday():
    return date.today() - timedelta(days=1)
