"""Validations métier réutilisables (formats §3.4 + logique tennistique).

NB pédagogique : ce module est la cible du bug BUG-F1 dans la version dégradée.
Ici, version SAINE = validation complète de la logique d'un set de padel/tennis.
"""
import re

LICENSE_RE = re.compile(r"^L\d{6}$")
EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
NAME_RE = re.compile(r"^[a-zA-ZÀ-ÿ\s'-]{2,50}$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

# Forme générale : "X-Y, X-Y" ou "X-Y, X-Y, X-Y"
SCORE_SHAPE_RE = re.compile(r"^(\d+-\d+)(,\s*\d+-\d+){1,2}$")


def is_valid_license(value: str) -> bool:
    return bool(LICENSE_RE.match(value or ""))


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value or ""))


def is_valid_name(value: str) -> bool:
    return bool(NAME_RE.match(value or ""))


def is_valid_time(value: str) -> bool:
    return bool(TIME_RE.match(value or ""))


def _is_valid_set(games_a: int, games_b: int) -> bool:
    """Un set est valide si le vainqueur atteint 6 jeux (l'autre <= 4),
    ou gagne 7-5, ou gagne 7-6 (tie-break). Pas d'égalité possible.
    """
    if games_a == games_b:
        return False
    winner, loser = max(games_a, games_b), min(games_a, games_b)
    if winner == 6:
        return loser <= 4
    if winner == 7:
        return loser in (5, 6)
    return False


def validate_score(score: str) -> bool:
    """Valide un score complet de padel (au meilleur de 3 sets).

    Vérifie la forme ET la logique de chaque set. Le vainqueur du match
    doit avoir remporté la majorité des sets joués.
    Exemples valides : "6-4, 6-3", "6-4, 3-6, 7-5", "7-6, 7-6".
    Exemples invalides : "3-2, 1-0", "8-3, 9-2", "6-4" (1 seul set).
    """
    if not score or not SCORE_SHAPE_RE.match(score.strip()):
        return False

    sets = [s.strip() for s in score.split(",")]
    if not 2 <= len(sets) <= 3:
        return False

    wins_a = wins_b = 0
    for s in sets:
        a_str, b_str = s.split("-")
        a, b = int(a_str), int(b_str)
        if not _is_valid_set(a, b):
            return False
        if a > b:
            wins_a += 1
        else:
            wins_b += 1

    # Un seul vainqueur, au meilleur de 3 (donc 2 sets gagnants requis).
    if wins_a == wins_b:
        return False
    sets_to_win = 2
    return max(wins_a, wins_b) == sets_to_win
