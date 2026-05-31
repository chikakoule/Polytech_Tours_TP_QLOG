"""Sérialiseurs : transforment les modèles ORM en dicts conformes aux exemples
JSON du cahier des charges (§3.3)."""
from app.models import Event, Match, Player, Pool, Team


def player_brief(player: Player) -> dict:
    return {
        "id": player.id,
        "first_name": player.first_name,
        "last_name": player.last_name,
    }


def player_full(player: Player, has_account: bool | None = None) -> dict:
    data = {
        "id": player.id,
        "first_name": player.first_name,
        "last_name": player.last_name,
        "company": player.company,
        "license_number": player.license_number,
        "birth_date": player.birth_date.isoformat() if player.birth_date else None,
        "photo_url": player.photo_url,
    }
    if has_account is not None:
        data["has_account"] = has_account
    else:
        data["has_account"] = player.user_id is not None
    return data


def pool_brief(pool: Pool | None) -> dict | None:
    if pool is None:
        return None
    return {"id": pool.id, "name": pool.name}


def team_out(team: Team) -> dict:
    return {
        "id": team.id,
        "company": team.company,
        "players": [player_brief(team.player1), player_brief(team.player2)],
        "pool": pool_brief(team.pool),
    }


def team_with_players_full(team: Team) -> dict:
    """Variante utilisée dans la liste des matchs (joueurs nommés)."""
    return {
        "id": team.id,
        "company": team.company,
        "players": [
            {
                "id": team.player1.id,
                "first_name": team.player1.first_name,
                "last_name": team.player1.last_name,
            },
            {
                "id": team.player2.id,
                "first_name": team.player2.first_name,
                "last_name": team.player2.last_name,
            },
        ],
    }


def match_out(match: Match) -> dict:
    return {
        "id": match.id,
        "event": {
            "id": match.event.id,
            "date": match.event.event_date.isoformat(),
            "time": match.event.event_time,
        },
        "court_number": match.court_number,
        "team1": team_with_players_full(match.team1),
        "team2": team_with_players_full(match.team2),
        "status": match.status,
        "score_team1": match.score_team1,
        "score_team2": match.score_team2,
    }


def match_in_event(match: Match) -> dict:
    return {
        "id": match.id,
        "court_number": match.court_number,
        "team1": team_with_players_full(match.team1),
        "team2": team_with_players_full(match.team2),
        "status": match.status,
        "score_team1": match.score_team1,
        "score_team2": match.score_team2,
    }


def event_out(event: Event) -> dict:
    return {
        "id": event.id,
        "event_date": event.event_date.isoformat(),
        "event_time": event.event_time,
        "matches": [match_in_event(m) for m in event.matches],
    }
