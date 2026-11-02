"""
End-to-End API Test for Farmer Advisory FastAPI Server.
Verifies /api/health, /api/languages, /api/quick-prompts, and /api/advisory.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api():
    print("Testing /api/health...")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health_data = res.json()
    print("Health response:", health_data)

    print("\nTesting /api/languages...")
    res = client.get("/api/languages")
    assert res.status_code == 200
    langs = res.json()
    print("Supported languages count:", len(langs))

    print("\nTesting /api/quick-prompts for Hindi...")
    res = client.get("/api/quick-prompts?lang=hi")
    assert res.status_code == 200
    prompts = res.json()
    print("Quick prompts received:", len(prompts))

    print("\nTesting /api/advisory for Hindi query...")
    req_body = {
        "query": "कपास की बुवाई किस महीने में करनी चाहिए?",
        "language": "hi",
        "mode": "demo"
    }
    res = client.post("/api/advisory", json=req_body)
    assert res.status_code == 200, f"Advisory post failed: {res.text}"
    adv_data = res.json()
    print("Advisory result:")
    print("Language:", adv_data["language_display"])
    print("Groundedness:", adv_data["groundedness_score"])
    print("Advisory excerpt:", adv_data["advisory"][:180])
    print("Action plan steps:", len(adv_data["action_plan"]))
    print("Sources cited count:", len(adv_data["sources"]))

    print("\nALL API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_api()
