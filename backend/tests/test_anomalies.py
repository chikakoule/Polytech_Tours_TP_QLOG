"""SUITE DE DÉTECTION DES 10 ANOMALIES VOLONTAIRES (référence enseignant).

Chaque test cible un bug précis de bugs-intentionnels.html.
  - Sur l'application SAINE : tous ces tests PASSENT (vert).
  - Sur la version DÉGRADÉE : le test correspondant ÉCHOUE (rouge), prouvant
    l'anomalie. C'est la grille de correction automatisée.

Bugs front (BUG-F5 filtre, BUG-S2 XSS rendu) : détectés côté Cypress.
BUG-F5 a aussi une dimension API testable ici (paramètre my_matches).
"""
from datetime import timedelta

from datetime import datetime, timezone

from jose import jwt

from app.config import settings


def _two_teams(make_players, make_team, companies):
    teams = []
    for i, c in enumerate(companies):
        pl = make_players(c, 2, start_license=500000 + i * 10)
        teams.append(make_team(c, pl[0], pl[1]))
    return teams


# ─────────────────────────── BUG-F1 ───────────────────────────
def test_bug_f1_score_logique_invalide_refusee(
    client, admin_headers, make_players, make_team, make_match, yesterday
):
    """Un score tennistiquement impossible doit être refusé (400)."""
    teams = _two_teams(make_players, make_team, ["F1 A", "F1 B"])
    mid = make_match(teams[0], teams[1], yesterday)
    r = client.put(
        f"/api/v1/matches/{mid}",
        json={"status": "TERMINE", "score_team1": "3-2, 1-0", "score_team2": "2-3, 0-1"},
        headers=admin_headers,
    )
    assert r.status_code == 400, "Le score '3-2, 1-0' devrait être rejeté (BUG-F1)"


# ─────────────────────────── BUG-F2 ───────────────────────────
def test_bug_f2_evenement_passe_refuse(
    client, admin_headers, make_players, make_team, yesterday
):
    """Le serveur doit refuser un événement à une date passée (400)."""
    teams = _two_teams(make_players, make_team, ["F2 A", "F2 B"])
    r = client.post(
        "/api/v1/events",
        json={
            "event_date": yesterday.isoformat(),
            "event_time": "19:30",
            "matches": [{"court_number": 1, "team1_id": teams[0], "team2_id": teams[1]}],
        },
        headers=admin_headers,
    )
    assert r.status_code == 400, "Un événement daté d'hier devrait être refusé (BUG-F2)"


# ─────────────────────────── BUG-F3 ───────────────────────────
def test_bug_f3_conflit_de_piste_detecte(
    client, admin_headers, make_players, make_team, tomorrow
):
    """Deux matchs sur la même piste au même créneau → conflit (409)."""
    teams = _two_teams(make_players, make_team, ["F3 A", "F3 B", "F3 C", "F3 D"])
    base = {
        "event_date": tomorrow.isoformat(),
        "event_time": "19:30",
        "court_number": 1,
    }
    r1 = client.post(
        "/api/v1/matches",
        json={**base, "team1_id": teams[0], "team2_id": teams[1]},
        headers=admin_headers,
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/api/v1/matches",
        json={**base, "team1_id": teams[2], "team2_id": teams[3]},
        headers=admin_headers,
    )
    assert r2.status_code == 409, "La 2e réservation de la piste 1 devrait être refusée (BUG-F3)"


# ─────────────────────────── BUG-F4 ───────────────────────────
def test_bug_f4_suppression_match_termine_refusee(
    client, admin_headers, make_players, make_team, make_match, yesterday
):
    """Un match TERMINE ne doit pas être supprimable (409)."""
    teams = _two_teams(make_players, make_team, ["F4 A", "F4 B"])
    mid = make_match(
        teams[0], teams[1], yesterday, status="TERMINE",
        score1="6-4, 6-3", score2="4-6, 3-6",
    )
    r = client.delete(f"/api/v1/matches/{mid}", headers=admin_headers)
    assert r.status_code == 409, "La suppression d'un match TERMINE devrait être refusée (BUG-F4)"


# ─────────────────────────── BUG-F5 (côté API) ───────────────────────────
def test_bug_f5_filtre_mes_matchs_api(
    client, player_user, player_headers, db_session, make_players, make_team, make_match, tomorrow
):
    """my_matches=true ne doit renvoyer que les matchs du joueur connecté."""
    from app.models import Player

    jean = db_session.query(Player).filter(Player.email == "joueur@padel.com").first()
    mate = make_players("Tech Corp", 1, start_license=510000)[0]
    my_team = make_team("Tech Corp", jean.id, mate)
    others = _two_teams(make_players, make_team, ["O1", "O2"])
    # 1 match du joueur + 1 match sans lui.
    make_match(my_team, others[0], tomorrow, court=1, status="A_VENIR")
    make_match(others[0], others[1], tomorrow, court=2, status="A_VENIR")

    mine = client.get("/api/v1/matches", params={"my_matches": "true"}, headers=player_headers)
    allm = client.get("/api/v1/matches", headers=player_headers)
    assert mine.json()["total"] == 1, "my_matches devrait filtrer sur l'équipe du joueur (BUG-F5)"
    assert allm.json()["total"] == 2


# ─────────────────────────── BUG-S1 ───────────────────────────
def test_bug_s1_route_admin_interdite_au_joueur(client, player_headers, player_user, db_session):
    """Un JOUEUR ne doit pas pouvoir appeler une route /admin/* (403)."""
    from app.models import Player

    p = Player(
        first_name="Sans", last_name="Compte", company="X Corp",
        license_number="L600001", email="sans.compte@x.fr",
    )
    db_session.add(p)
    db_session.commit()
    r = client.post(
        "/api/v1/admin/accounts/create",
        json={"player_id": p.id, "role": "JOUEUR"},
        headers=player_headers,
    )
    assert r.status_code == 403, "Un joueur ne doit pas créer de compte admin (BUG-S1)"


# ─────────────────────────── BUG-S3 ───────────────────────────
def test_bug_s3_blocage_au_cinquieme_echec(client, admin_user):
    """Après 5 échecs, le compte doit être bloqué (403), pas au 6e."""
    last = None
    for _ in range(5):
        last = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@padel.com", "password": "mauvais"},
        )
    assert last.status_code == 403, "Le 5e échec devrait bloquer le compte (BUG-S3)"


def test_bug_s3_compteur_reset_apres_succes(client, admin_user):
    """Le compteur d'échecs se réinitialise après une connexion réussie."""
    for _ in range(4):
        client.post("/api/v1/auth/login", json={"email": "admin@padel.com", "password": "mauvais"})
    ok = client.post("/api/v1/auth/login", json={"email": "admin@padel.com", "password": "Admin@2025!"})
    assert ok.status_code == 200
    # Après reset, un nouvel échec doit repartir à 4 tentatives restantes.
    r = client.post("/api/v1/auth/login", json={"email": "admin@padel.com", "password": "mauvais"})
    assert r.json()["detail"]["attempts_remaining"] == 4, "Le compteur doit se réinitialiser (BUG-S3)"


# ─────────────────────────── BUG-S4 ───────────────────────────
def test_bug_s4_message_login_generique(client, admin_user):
    """Le message d'erreur doit être identique que l'email existe ou non."""
    inconnu = client.post(
        "/api/v1/auth/login", json={"email": "inexistant@nulle.part", "password": "x"}
    )
    connu = client.post(
        "/api/v1/auth/login", json={"email": "admin@padel.com", "password": "mauvais"}
    )
    msg_inconnu = inconnu.json()["detail"]["detail"]
    msg_connu = connu.json()["detail"]["detail"]
    assert msg_inconnu == msg_connu, "Les messages doivent être identiques (BUG-S4)"


# ─────────────────────────── BUG-S5 ───────────────────────────
def test_bug_s5_token_expire_refuse(client, admin_user, db_session):
    """Un JWT expiré doit être refusé (401)."""
    from app.models import User

    admin = db_session.query(User).filter(User.email == "admin@padel.com").first()
    expired = jwt.encode(
        {
            "sub": str(admin.id),
            "email": admin.email,
            "role": admin.role,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    r = client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401, "Un token expiré doit être rejeté (BUG-S5)"
