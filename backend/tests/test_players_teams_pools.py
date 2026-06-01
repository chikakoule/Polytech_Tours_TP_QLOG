"""Tests fonctionnels : joueurs, équipes, poules (CRUD + règles métier)."""


def _create_player(client, headers, **over):
    payload = {
        "first_name": "Alice",
        "last_name": "Martin",
        "company": "Tech Corp",
        "license_number": "L555001",
        "email": "alice.martin@tc.fr",
    }
    payload.update(over)
    return client.post("/api/v1/players", json=payload, headers=headers)


def test_create_player_ok(client, admin_headers):
    r = _create_player(client, admin_headers)
    assert r.status_code == 201
    assert r.json()["license_number"] == "L555001"


def test_create_player_invalid_license(client, admin_headers):
    r = _create_player(client, admin_headers, license_number="ABC")
    assert r.status_code == 422


def test_create_player_duplicate_license(client, admin_headers):
    _create_player(client, admin_headers)
    r = _create_player(client, admin_headers, email="autre@tc.fr")
    assert r.status_code == 409


def test_list_players_requires_admin(client, player_headers):
    assert client.get("/api/v1/players", headers=player_headers).status_code == 403


def test_delete_player_in_team_refused(client, admin_headers, make_players, make_team):
    ids = make_players("Tech Corp", 2)
    make_team("Tech Corp", ids[0], ids[1])
    r = client.delete(f"/api/v1/players/{ids[0]}", headers=admin_headers)
    assert r.status_code == 409


def test_create_team_ok(client, admin_headers, make_players):
    ids = make_players("Tech Corp", 2)
    r = client.post(
        "/api/v1/teams",
        json={"company": "Tech Corp", "player1_id": ids[0], "player2_id": ids[1]},
        headers=admin_headers,
    )
    assert r.status_code == 201


def test_create_team_different_companies_refused(client, admin_headers, make_players):
    a = make_players("Tech Corp", 1, start_license=210000)
    b = make_players("Innov Ltd", 1, start_license=220000)
    r = client.post(
        "/api/v1/teams",
        json={"company": "Tech Corp", "player1_id": a[0], "player2_id": b[0]},
        headers=admin_headers,
    )
    assert r.status_code == 400


def test_player_in_two_teams_refused(client, admin_headers, make_players, make_team):
    ids = make_players("Tech Corp", 3)
    make_team("Tech Corp", ids[0], ids[1])
    r = client.post(
        "/api/v1/teams",
        json={"company": "Tech Corp", "player1_id": ids[0], "player2_id": ids[2]},
        headers=admin_headers,
    )
    assert r.status_code == 409


def _six_teams(make_players, make_team):
    team_ids = []
    for i in range(6):
        ids = make_players(f"Comp{i}", 2, start_license=300000 + i * 10)
        team_ids.append(make_team(f"Comp{i}", ids[0], ids[1]))
    return team_ids


def test_create_pool_exactly_six(client, admin_headers, make_players, make_team):
    team_ids = _six_teams(make_players, make_team)
    r = client.post(
        "/api/v1/pools",
        json={"name": "Poule A", "team_ids": team_ids},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["teams_count"] == 6


def test_create_pool_wrong_count_refused(client, admin_headers, make_players, make_team):
    team_ids = _six_teams(make_players, make_team)
    r = client.post(
        "/api/v1/pools",
        json={"name": "Poule B", "team_ids": team_ids[:5]},
        headers=admin_headers,
    )
    assert r.status_code == 400


def test_pool_create_requires_admin(client, player_headers):
    assert (
        client.post(
            "/api/v1/pools", json={"name": "X", "team_ids": [1, 2, 3, 4, 5, 6]}, headers=player_headers
        ).status_code
        == 403
    )
