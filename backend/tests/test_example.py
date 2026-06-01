"""Test d'exemple — point de départ pour vos tests pytest.

Lancez la suite avec :
    pytest
    pytest --cov=app --cov-report=term-missing   # avec couverture

À vous d'écrire les tests des endpoints (auth, joueurs, équipes, poules,
événements, matchs, résultats…), des validations métier et des règles de
sécurité. Vous pouvez utiliser le TestClient de FastAPI :

    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    r = client.post("/api/v1/auth/login", json={"email": "...", "password": "..."})
"""


def test_exemple_qui_passe():
    """Test trivial fourni pour vérifier que pytest est bien configuré."""
    assert 1 + 1 == 2
