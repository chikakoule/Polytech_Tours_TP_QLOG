"""Calcul du classement des entreprises et des résultats personnels (§2.5)."""
from sqlalchemy.orm import Session

from app.models import Match, Player, Team

POINTS_WIN = 3
POINTS_LOSS = 0


def parse_sets(score: str | None) -> list[tuple[int, int]]:
    """'6-4, 6-3' -> [(6, 4), (6, 3)]. Tolérant en lecture."""
    if not score:
        return []
    sets = []
    for part in score.split(","):
        part = part.strip()
        if "-" not in part:
            continue
        a, b = part.split("-")
        try:
            sets.append((int(a), int(b)))
        except ValueError:
            continue
    return sets


def sets_won_by_team1(score_team1: str | None) -> tuple[int, int]:
    """Renvoie (sets gagnés par team1, sets gagnés par team2)."""
    won = lost = 0
    for a, b in parse_sets(score_team1):
        if a > b:
            won += 1
        elif b > a:
            lost += 1
    return won, lost


def compute_rankings(db: Session) -> list[dict]:
    """Classement des entreprises sur les matchs TERMINE.

    Tri : points desc, victoires desc, diff. de sets desc, nom alphabétique.
    """
    stats: dict[str, dict] = {}

    def bucket(company: str) -> dict:
        return stats.setdefault(
            company,
            {
                "company": company,
                "matches_played": 0,
                "wins": 0,
                "losses": 0,
                "points": 0,
                "sets_won": 0,
                "sets_lost": 0,
            },
        )

    finished = db.query(Match).filter(Match.status == "TERMINE").all()
    for m in finished:
        c1 = m.team1.company
        c2 = m.team2.company
        t1_sets, t2_sets = sets_won_by_team1(m.score_team1)

        b1, b2 = bucket(c1), bucket(c2)
        b1["matches_played"] += 1
        b2["matches_played"] += 1
        b1["sets_won"] += t1_sets
        b1["sets_lost"] += t2_sets
        b2["sets_won"] += t2_sets
        b2["sets_lost"] += t1_sets

        if t1_sets > t2_sets:
            b1["wins"] += 1
            b1["points"] += POINTS_WIN
            b2["losses"] += 1
        elif t2_sets > t1_sets:
            b2["wins"] += 1
            b2["points"] += POINTS_WIN
            b1["losses"] += 1

    ranking = sorted(
        stats.values(),
        key=lambda s: (
            -s["points"],
            -s["wins"],
            -(s["sets_won"] - s["sets_lost"]),
            s["company"].lower(),
        ),
    )
    for position, row in enumerate(ranking, start=1):
        row["position"] = position
    # Réordonne les clés pour coller à l'exemple (position en tête).
    return [
        {
            "position": r["position"],
            "company": r["company"],
            "matches_played": r["matches_played"],
            "wins": r["wins"],
            "losses": r["losses"],
            "points": r["points"],
            "sets_won": r["sets_won"],
            "sets_lost": r["sets_lost"],
        }
        for r in ranking
    ]


def player_team_ids(db: Session, player_id: int) -> list[int]:
    teams = (
        db.query(Team)
        .filter((Team.player1_id == player_id) | (Team.player2_id == player_id))
        .all()
    )
    return [t.id for t in teams]


def compute_my_results(db: Session, player: Player) -> dict:
    """Résultats personnels (matchs TERMINE) + statistiques d'un joueur."""
    team_ids = player_team_ids(db, player.id)
    results = []
    wins = losses = 0

    if team_ids:
        matches = (
            db.query(Match)
            .filter(Match.status == "TERMINE")
            .filter((Match.team1_id.in_(team_ids)) | (Match.team2_id.in_(team_ids)))
            .all()
        )
        # Du plus récent au plus ancien.
        matches.sort(
            key=lambda m: (m.event.event_date, m.event.event_time), reverse=True
        )
        for m in matches:
            is_team1 = m.team1_id in team_ids
            my_team = m.team1 if is_team1 else m.team2
            opp_team = m.team2 if is_team1 else m.team1
            my_score = m.score_team1 if is_team1 else m.score_team2
            t1_sets, t2_sets = sets_won_by_team1(m.score_team1)
            my_sets = t1_sets if is_team1 else t2_sets
            opp_sets = t2_sets if is_team1 else t1_sets
            won = my_sets > opp_sets
            if won:
                wins += 1
            else:
                losses += 1
            results.append(
                {
                    "match_id": m.id,
                    "date": m.event.event_date.isoformat(),
                    "opponents": {
                        "company": opp_team.company,
                        "players": [
                            f"{opp_team.player1.first_name} {opp_team.player1.last_name}",
                            f"{opp_team.player2.first_name} {opp_team.player2.last_name}",
                        ],
                    },
                    "score": my_score,
                    "result": "VICTOIRE" if won else "DEFAITE",
                    "court_number": m.court_number,
                }
            )

    total = wins + losses
    win_rate = round((wins / total) * 100, 1) if total else 0.0
    return {
        "results": results,
        "statistics": {
            "total_matches": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
        },
    }
