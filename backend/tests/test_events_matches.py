"""Tests fonctionnels : événements, matchs, résultats, classement."""
from datetime import timedelta


def _two_teams(make_players, make_team, n=4):
    ids = []
    teams = []
    companies = ["A Corp", "B Corp", "C Corp", "D Corp"]
    for i in range(n):
        pl = make_players(companies[i], 2, start_license=400000 + i * 10)
        teams.append(make_team(companies[i], pl[0], pl[1]))
    return teams


def test_create_event_future_ok(client, admin_headers, make_players, make_team, tomorrow):
    teams = _two_teams(make_players, make_team, 2)
    r = client.post(
        "/api/v1/events",
        json={
            "event_date": tomorrow.isoformat(),
            "event_time": "19:30",
            "matches": [{"court_number": 1, "team1_id": teams[0], "team2_id": teams[1]}],
        },
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert len(r.json()["matches"]) == 1


def test_create_event_duplicate_court_refused(client, admin_headers, make_players, make_team, tomorrow):
    teams = _two_teams(make_players, make_team, 4)
    r = client.post(
        "/api/v1/events",
        json={
            "event_date": tomorrow.isoformat(),
            "event_time": "19:30",
            "matches": [
                {"court_number": 1, "team1_id": teams[0], "team2_id": teams[1]},
                {"court_number": 1, "team1_id": teams[2], "team2_id": teams[3]},
            ],
        },
        headers=admin_headers,
    )
    assert r.status_code == 400


def test_create_event_team_twice_refused(client, admin_headers, make_players, make_team, tomorrow):
    teams = _two_teams(make_players, make_team, 3)
    r = client.post(
        "/api/v1/events",
        json={
            "event_date": tomorrow.isoformat(),
            "event_time": "19:30",
            "matches": [
                {"court_number": 1, "team1_id": teams[0], "team2_id": teams[1]},
                {"court_number": 2, "team1_id": teams[0], "team2_id": teams[2]},
            ],
        },
        headers=admin_headers,
    )
    assert r.status_code == 400


def test_create_match_requires_admin(client, player_headers, tomorrow):
    r = client.post(
        "/api/v1/matches",
        json={
            "event_date": tomorrow.isoformat(),
            "event_time": "19:30",
            "court_number": 1,
            "team1_id": 1,
            "team2_id": 2,
        },
        headers=player_headers,
    )
    assert r.status_code == 403


def test_update_match_score_valid(client, admin_headers, make_players, make_team, make_match, yesterday):
    teams = _two_teams(make_players, make_team, 2)
    mid = make_match(teams[0], teams[1], yesterday)
    r = client.put(
        f"/api/v1/matches/{mid}",
        json={"status": "TERMINE", "score_team1": "6-4, 6-3", "score_team2": "4-6, 3-6"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "TERMINE"


def test_delete_upcoming_match_ok(client, admin_headers, make_players, make_team, make_match, tomorrow):
    teams = _two_teams(make_players, make_team, 2)
    mid = make_match(teams[0], teams[1], tomorrow, status="A_VENIR")
    assert client.delete(f"/api/v1/matches/{mid}", headers=admin_headers).status_code == 204


def test_matches_upcoming_filter(client, admin_headers, make_players, make_team, make_match, today):
    teams = _two_teams(make_players, make_team, 2)
    make_match(teams[0], teams[1], today + timedelta(days=2), status="A_VENIR")
    make_match(teams[0], teams[1], today + timedelta(days=60), court=2, status="A_VENIR")
    r = client.get("/api/v1/matches", params={"upcoming": "true"}, headers=admin_headers)
    assert r.status_code == 200
    # Seul le match dans les 30 prochains jours doit ressortir.
    assert r.json()["total"] == 1


def test_rankings_structure(client, admin_headers, make_players, make_team, make_match, yesterday):
    teams = _two_teams(make_players, make_team, 2)
    make_match(teams[0], teams[1], yesterday, status="TERMINE", score1="6-4, 6-3", score2="4-6, 3-6")
    r = client.get("/api/v1/results/rankings", headers=admin_headers)
    assert r.status_code == 200
    rankings = r.json()["rankings"]
    assert rankings[0]["points"] == 3  # le vainqueur
    assert {row["company"] for row in rankings} == {"A Corp", "B Corp"}


def test_my_results_for_player(client, player_user, player_headers, db_session, make_players, make_team, make_match, yesterday):
    # Le joueur de test (Tech Corp) doit avoir une équipe pour avoir des résultats.
    from app.models import Player

    jean = db_session.query(Player).filter(Player.email == "joueur@padel.com").first()
    mate = make_players("Tech Corp", 1, start_license=410000)[0]
    my_team = make_team("Tech Corp", jean.id, mate)
    opp = _two_teams(make_players, make_team, 1)[0]
    make_match(my_team, opp, yesterday, status="TERMINE", score1="6-2, 6-1", score2="2-6, 1-6")
    r = client.get("/api/v1/results/my-results", headers=player_headers)
    assert r.status_code == 200
    assert r.json()["statistics"]["wins"] == 1
