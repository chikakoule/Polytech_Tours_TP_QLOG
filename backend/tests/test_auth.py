"""Tests d'authentification : login, JWT, changement de mot de passe, protection."""
from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD


def test_login_success(client, admin_user):
    r = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["role"] == "ADMINISTRATEUR"


def test_login_wrong_password(client, admin_user):
    r = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "mauvais"})
    assert r.status_code == 401
    detail = r.json()["detail"]
    assert detail["attempts_remaining"] == 4


def test_protected_route_without_token(client):
    assert client.get("/api/v1/profile/me").status_code == 401


def test_protected_route_with_token(client, admin_headers):
    assert client.get("/api/v1/profile/me", headers=admin_headers).status_code == 200


def test_change_password_success(client, player_user, player_headers):
    r = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "Joueur@2025!",
            "new_password": "NouveauP@ss2025!",
            "confirm_password": "NouveauP@ss2025!",
        },
        headers=player_headers,
    )
    assert r.status_code == 200


def test_change_password_mismatch(client, player_user, player_headers):
    r = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "Joueur@2025!",
            "new_password": "NouveauP@ss2025!",
            "confirm_password": "Different@2025!",
        },
        headers=player_headers,
    )
    assert r.status_code == 400


def test_change_password_weak(client, player_user, player_headers):
    r = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "Joueur@2025!",
            "new_password": "faible",
            "confirm_password": "faible",
        },
        headers=player_headers,
    )
    assert r.status_code == 400


def test_change_password_wrong_current(client, player_user, player_headers):
    r = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "PasLeBon@2025!",
            "new_password": "NouveauP@ss2025!",
            "confirm_password": "NouveauP@ss2025!",
        },
        headers=player_headers,
    )
    assert r.status_code == 400
