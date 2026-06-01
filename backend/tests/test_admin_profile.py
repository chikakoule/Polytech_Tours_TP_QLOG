"""Tests : administration des comptes et profil utilisateur."""


def test_admin_creates_account_for_player(client, admin_headers, db_session):
    from app.models import Player

    p = Player(
        first_name="Sans", last_name="Compte", company="X Corp",
        license_number="L600100", email="sans.compte@x.fr",
    )
    db_session.add(p)
    db_session.commit()

    r = client.post(
        "/api/v1/admin/accounts/create",
        json={"player_id": p.id, "role": "JOUEUR"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "sans.compte@x.fr"
    # Mot de passe temporaire conforme à la politique (>= 12 caractères).
    assert len(body["temporary_password"]) >= 12


def test_admin_create_account_twice_refused(client, admin_headers, db_session):
    from app.models import Player

    p = Player(
        first_name="Deja", last_name="Compte", company="X Corp",
        license_number="L600101", email="deja.compte@x.fr",
    )
    db_session.add(p)
    db_session.commit()
    first = client.post(
        "/api/v1/admin/accounts/create",
        json={"player_id": p.id, "role": "JOUEUR"},
        headers=admin_headers,
    )
    assert first.status_code == 201
    second = client.post(
        "/api/v1/admin/accounts/create",
        json={"player_id": p.id, "role": "JOUEUR"},
        headers=admin_headers,
    )
    assert second.status_code == 409


def test_admin_create_account_unknown_player(client, admin_headers):
    r = client.post(
        "/api/v1/admin/accounts/create",
        json={"player_id": 99999, "role": "JOUEUR"},
        headers=admin_headers,
    )
    assert r.status_code == 404


def test_admin_reset_password(client, admin_headers, player_user, db_session):
    from app.models import User

    user = db_session.query(User).filter(User.email == "joueur@padel.com").first()
    r = client.post(f"/api/v1/admin/accounts/{user.id}/reset-password", headers=admin_headers)
    assert r.status_code == 200
    assert len(r.json()["temporary_password"]) >= 12


def test_reset_password_requires_admin(client, player_headers):
    assert (
        client.post("/api/v1/admin/accounts/1/reset-password", headers=player_headers).status_code
        == 403
    )


def test_get_profile_me(client, player_headers):
    r = client.get("/api/v1/profile/me", headers=player_headers)
    assert r.status_code == 200
    assert r.json()["player"]["license_number"] == "L100001"


def test_update_profile_ok(client, player_headers):
    r = client.put(
        "/api/v1/profile/me",
        json={
            "first_name": "Jean-Pierre",
            "last_name": "Joueur",
            "email": "joueur@padel.com",
            "birth_date": "1990-05-15",
        },
        headers=player_headers,
    )
    assert r.status_code == 200
    assert r.json()["player"]["first_name"] == "Jean-Pierre"


def test_update_profile_underage_refused(client, player_headers):
    from datetime import date

    too_young = date.today().replace(year=date.today().year - 10).isoformat()
    r = client.put(
        "/api/v1/profile/me",
        json={
            "first_name": "Jean",
            "last_name": "Joueur",
            "email": "joueur@padel.com",
            "birth_date": too_young,
        },
        headers=player_headers,
    )
    assert r.status_code == 422


def test_update_profile_duplicate_email_refused(client, player_headers, admin_user):
    # admin_user occupe déjà admin@padel.com
    r = client.put(
        "/api/v1/profile/me",
        json={"first_name": "Jean", "last_name": "Joueur", "email": "admin@padel.com"},
        headers=player_headers,
    )
    assert r.status_code == 409


def test_delete_photo_when_none(client, player_headers):
    r = client.delete("/api/v1/profile/me/photo", headers=player_headers)
    assert r.status_code == 200
