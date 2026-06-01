"""Tests unitaires des validateurs métier (formats + logique de score)."""
import pytest

from app.validators import (
    is_valid_email,
    is_valid_license,
    is_valid_name,
    is_valid_time,
    validate_score,
)


@pytest.mark.parametrize("value", ["L123456", "L000001", "L999999"])
def test_license_valid(value):
    assert is_valid_license(value)


@pytest.mark.parametrize("value", ["123456", "L12345", "L1234567", "X123456", "L12345A", ""])
def test_license_invalid(value):
    assert not is_valid_license(value)


@pytest.mark.parametrize("value", ["a@b.fr", "john.doe@example.com", "x+y@sub.domain.org"])
def test_email_valid(value):
    assert is_valid_email(value)


@pytest.mark.parametrize("value", ["plainaddress", "@no-local.com", "no-at.fr", "a@b"])
def test_email_invalid(value):
    assert not is_valid_email(value)


@pytest.mark.parametrize("value", ["Jean", "Marie-Claire", "O'Connor", "Jean Paul", "Éloïse"])
def test_name_valid(value):
    assert is_valid_name(value)


@pytest.mark.parametrize("value", ["J", "A" * 51, "Jean123", "Jean@"])
def test_name_invalid(value):
    assert not is_valid_name(value)


@pytest.mark.parametrize("value", ["00:00", "19:30", "23:59"])
def test_time_valid(value):
    assert is_valid_time(value)


@pytest.mark.parametrize("value", ["24:00", "19:60", "9:30", "1930"])
def test_time_invalid(value):
    assert not is_valid_time(value)


# ── Logique de score (au cœur de BUG-F1) ──
@pytest.mark.parametrize("score", ["6-4, 6-3", "6-4, 3-6, 7-5", "7-6, 7-6", "6-0, 6-0", "7-5, 6-7, 6-4"])
def test_score_valid(score):
    assert validate_score(score), f"devrait être valide : {score}"


@pytest.mark.parametrize(
    "score",
    [
        "3-2, 1-0",   # aucun set gagnant à 6
        "8-3, 9-2",   # scores impossibles
        "6-4",        # un seul set
        "6-4, 6-4, 6-4",  # 3 sets gagnés par le même = impossible (2 suffisent)
        "6-6, 6-6",   # égalité impossible
        "6-4, 5-5",   # 2e set sans vainqueur
        "",
    ],
)
def test_score_invalid(score):
    assert not validate_score(score), f"devrait être invalide : {score}"
