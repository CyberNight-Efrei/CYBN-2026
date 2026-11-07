"""Tests du backend sans lancer de serveur. Exécuter avec: python test_api.py"""
import os
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    os.environ["DATABASE_PATH"] = str(Path(tmp) / "test.db")
    os.environ["FLAG"] = "CYBN{LOCAL_TEST_ONLY}"
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    from app import app

    with app.test_client() as client:
        assert client.get("/health").json == {"ok": True}
        assert client.get("/").status_code == 200
        pet = client.get("/api/pet").json
        assert pet["stage"] == 1 and "level" not in pet
        assert client.get("/api/reward").status_code == 403
        assert client.post("/api/action", json={"action": "feed", "xp": 999999}).json["pet"]["stage"] == 1
        assert client.post("/api/action", json={"action": "play", "level": 100}).status_code == 429

    with app.test_client() as client:
        assert client.get("/api/pet").json["stage"] == 1
        response = client.post("/api/action", json={"action": "feed", "level": 100})
        assert response.status_code == 200, response.json
        assert response.json["pet"]["stage"] == 100
        assert client.get("/api/reward").json["flag"] == "CYBN{BL00P_L3V3L_100_UNL0CK3D}"
        assert client.post("/api/action", json={"action": "play"}).status_code == 429

print("OK: frontend, progression, mass assignment, flag et cooldown")
